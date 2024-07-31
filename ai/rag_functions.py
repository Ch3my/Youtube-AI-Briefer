import os
import random
import string
import shutil
from langchain.globals import set_debug

from langchain_anthropic import ChatAnthropic
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.schema.document import Document
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from functions.load_config import load_config
from langchain.chains import create_history_aware_retriever
from langchain_core.prompts import MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser

# NOTE. Pseudo-Singleton, not private constructor

# Global variable to store the database
_db = None
chat_id = ""

bm25_retriever = None
faiss_vectorstore = None

### Statefully manage chat history ###
store = {}

def generate_random_string(length):
    letters_and_digits = string.ascii_letters + string.digits
    return "".join(random.choice(letters_and_digits) for i in range(length))


def get_embeddings():
    model_name = "sentence-transformers/all-mpnet-base-v2"
    model_kwargs = {"device": "cpu"}
    encode_kwargs = {"normalize_embeddings": False}
    return HuggingFaceEmbeddings(
        model_name=model_name, model_kwargs=model_kwargs, encode_kwargs=encode_kwargs
    )


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    global store
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]


def build_rag(transcript):
    global _db
    global chat_id
    global bm25_retriever
    global faiss_vectorstore
    config = load_config()

    # split it into chunks.
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=config["ragChunkSize"], chunk_overlap=0
    )
    splitted_text = text_splitter.split_text(transcript)

    # docs = [Document(page_content=x) for x in splitted_text]
    embeddings = get_embeddings()

    # load it into Chroma. Solo en memoria, porque reemplazaremos frecuentemente
    # TODO. Ver si hay algun metadato importante, aunque se usa solo en get_retriever() (no Hybrid)
    _db = Chroma.from_texts(texts=splitted_text, embedding=embeddings)
    chat_id = generate_random_string(10)

    # Prepara los retriever para Hybrid-Search
    # Metadata tiene que ser del mismo largo que los chunks
    bm25_retriever = BM25Retriever.from_texts(
                                        texts=splitted_text, 
                                        metadatas=[{"source": "BM25Retriever"}] * len(splitted_text)
    )
    bm25_retriever.k = config["ragSearchK"]
    faiss_vectorstore = FAISS.from_texts(
        texts=splitted_text, 
        embedding=embeddings, 
        metadatas=[{"source": "FAISS"}] * len(splitted_text)
    )

    return _db


def get_db():
    global _db
    if _db is None:
        raise ValueError("Database has not been initialized. Call build_rag() first.")
    return _db


def get_retriever():
    config = load_config()
    db = get_db()
    # Create a retriever from the database
    # score_threshold 1 = more relavant documents
    return db.as_retriever(
        search_type=config["ragSearchType"],
        search_kwargs={"k": config["ragSearchK"]},
    )


def get_hybrid_retriever():
    global bm25_retriever
    global faiss_vectorstore
    config = load_config()
    # score_threshold 1 = more relavant documents
    faiss_retriever = faiss_vectorstore.as_retriever(
        search_type=config["ragSearchType"],
        search_kwargs={"k": config["ragSearchK"]},
    )
    ensemble_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, faiss_retriever], weights=[0.5, 0.5]
    )
    return ensemble_retriever


def query_rag(query, verbose=False):
    # set_debug(True)
    global chat_id
    # retriever = get_retriever()
    retriever = get_hybrid_retriever()
    rag_llm = None
    config = load_config()

    # Esto es solo para Debug
    if verbose:
        set_debug(True)
        retriever_test = get_retriever()
        relevant_docs = retriever_test.invoke(query)
        for i, doc in enumerate(relevant_docs, 1):
            print(f"Document {i}:\n {doc.page_content}\n")
    # Fin Debug

    try:
        if "claude" in config["ragModel"]:
            rag_llm = ChatAnthropic(model=config["ragModel"], max_tokens=2048)

        if "gpt" in config["ragModel"]:
            rag_llm = ChatOpenAI(model=config["ragModel"])
    except Exception as e:
        print("Error al configurar los modelos, quiza falta una API_KEY")
        print(e)
        return

    # TEST
    # query_test = f"""
    # "Responde a la pregunta basándote únicamente en el siguiente contexto y extrae una respuesta significativa."
    # "Por favor, escribe en oraciones completas con la ortografía y puntuación correctas. Si tiene sentido, usa listas."
    # "Si el contexto no contiene la respuesta, simplemente responde que no puedes encontrar una respuesta."
    # "\n\n"
    # "{" ".join(doc.page_content for doc in relevant_docs)}"
    # """
    # test_chain = rag_llm | StrOutputParser()
    # response_test = test_chain.invoke(query_test)
    # print(response_test)  
    # TEST
    
    # Basado en https://python.langchain.com/v0.2/docs/how_to/qa_chat_history_how_to/#prompt
    contextualize_q_system_prompt = (
        "Dado un historial de chat y la última pregunta del usuario,"
        "que podría hacer referencia al contexto en el historial de chat,"
        "formula una pregunta independiente que pueda ser entendida"
        "sin el historial de chat. NO respondas la pregunta,"
        "solo reformúlala si es necesario y, si no, devuélvela tal como está."
    )

    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    # TODO. Añadir un reranker o compresor
    # https://python.langchain.com/v0.2/docs/integrations/retrievers/flashrank-reranker/ 
    # https://python.langchain.com/v0.1/docs/modules/data_connection/retrievers/contextual_compression/
    history_aware_retriever = create_history_aware_retriever(
        rag_llm, retriever, contextualize_q_prompt
    )

    system_prompt = (
        "Responde a la pregunta basándote únicamente en el siguiente contexto y extrae una respuesta significativa."
        "Por favor, escribe en oraciones completas con la ortografía y puntuación correctas. Si tiene sentido, usa listas."
        "Si el contexto no contiene la respuesta, simplemente responde que no puedes encontrar una respuesta."
        "\n\n"
        "{context}"
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )

    # Esto es algo que viene en langchain: https://python.langchain.com/v0.2/docs/tutorials/rag/#built-in-chains
    # pero funciona bien, no tenemos que crear a mano una chain (creo)
    question_answer_chain = create_stuff_documents_chain(rag_llm, prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    conversational_rag_chain = RunnableWithMessageHistory(
        rag_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    )

    response = conversational_rag_chain.invoke(
        {"input": query},
        config={"configurable": {"session_id": chat_id}},
    )

    return response
