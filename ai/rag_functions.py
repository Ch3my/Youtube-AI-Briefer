import os
import random
import string
import shutil
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

# NOTE. Pseudo-Singleton, not private constructor

# Global variable to store the database
_db = None
chat_id = ""

def generate_random_string(length):
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join(random.choice(letters_and_digits) for i in range(length))

def get_embeddings():
    model_name = "sentence-transformers/all-mpnet-base-v2"
    model_kwargs = {"device": "cpu"}
    encode_kwargs = {"normalize_embeddings": False}
    return HuggingFaceEmbeddings(
        model_name=model_name, model_kwargs=model_kwargs, encode_kwargs=encode_kwargs
    )


def build_rag(transcript):
    global _db
    global chat_id
    vector_db_directory = "./vector-db"
    config = load_config()

    # split it into chunks.
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=config["ragChunkSize"], chunk_overlap=0)
    docs = [Document(page_content=x) for x in text_splitter.split_text(transcript)]
    embeddings = get_embeddings()
  
    # Check if the directory exists and delete it. Aunque se supone que se sobreescribe solo
    # a veces llegan datos de otros videos
    if os.path.exists(vector_db_directory) and os.path.isdir(vector_db_directory):
        shutil.rmtree(vector_db_directory)
        
    # load it into Chroma
    _db = Chroma.from_documents(docs, embeddings, persist_directory="./vector-db")
    chat_id = generate_random_string(10)
    return _db


def get_db():
    global _db
    if _db is None:
        # If no db is loaded, load the existing one
        embeddings = get_embeddings()
        _db = Chroma(persist_directory="./vector-db", embedding_function=embeddings)
    return _db


def get_retriever():
    config = load_config()
    db = get_db()
    # Create a retriever from the database
    return db.as_retriever(
        search_type=config["ragSearchType"], search_kwargs={"k": config["ragSearchK"]}
    )


def query_rag(query, verbose=False):
    global chat_id
    retriever = get_retriever()
    rag_llm = None
    config = load_config()

    # Esto es solo para Debug
    relevant_docs = retriever.invoke(query)
    if verbose:
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
    # rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    # response = rag_chain.invoke({"input": query})
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    ### Statefully manage chat history ###
    store = {}

    def get_session_history(session_id: str) -> BaseChatMessageHistory:
        if session_id not in store:
            store[session_id] = ChatMessageHistory()
        return store[session_id]

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


# Example usage:
# transcript = "Your transcript text here"
# build_rag(transcript)  # Only need to call this once to create/update the database
# query_rag("de que trata el texto?")
# query_rag("otra pregunta")  # Will reuse the existing database
