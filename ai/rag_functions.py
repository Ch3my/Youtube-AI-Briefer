import random
import string
from uuid import uuid4
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
from ai.generate_tags import generate_tags
from functions.load_config import load_config
from langchain.chains import create_history_aware_retriever
from langchain_core.prompts import MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.retrievers import EnsembleRetriever
from langchain_core.retrievers import BaseRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from typing import List
from langchain.chains.query_constructor.base import AttributeInfo
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain.retrievers.document_compressors import FlashrankRerank
from langchain.retrievers import ContextualCompressionRetriever

# NOTE. Pseudo-Singleton, not private constructor

# Global variable to store the database
_db = None
chat_id = ""

bm25_retriever = None
faiss_vectorstore = None

### Statefully manage chat history ###
store = {}

metadata_field_info = [
    AttributeInfo(
        name="tags",
        description="keywords about the content of the chunk. Exaple ['jquery', 'react', 'donald', 'police', '1 million', 'yesterday', 'complain']",
        type="list",
    )
]


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
    embeddings = get_embeddings()

    # Config if create tags or not, build metadatas with [] if not
    uuids = [str(uuid4()) for _ in range(len(splitted_text))]
    metadatas = [
        {
            "tags": tags,
            "id": uuid,
            "tag_1": tags[0] if len(tags) > 0 else "",
            "tag_2": tags[1] if len(tags) > 1 else "",
            "tag_3": tags[2] if len(tags) > 2 else "",
        }
        for chunk, uuid in zip(splitted_text, uuids)
        if (tags := generate_tags("search", chunk) if config["useTags"] == "si" else [])
    ]

    # load it into Chroma. Solo en memoria, porque reemplazaremos frecuentemente
    # TODO. Ver si hay algun metadato importante, aunque se usa solo en get_retriever() (no Hybrid)
    # nota. se puede implementar busqueda por metadata a traves de chroma pero soporte solo datos
    # simples string number, etc, no podemos filtrar por arrays
    # https://github.com/langchain-ai/langchain/issues/7824
    # _db = Chroma.from_texts(texts=splitted_text, embedding=embeddings)

    chromadb_retriever_metadatas = [
        {"source": "ChromaDB", **meta} for meta in metadatas
    ]  # Combine with existing metadata
    docs = [
        Document(page_content=chunk, metadata=metadata)
        for chunk, metadata in zip(splitted_text, chromadb_retriever_metadatas)
    ]
    _db = Chroma.from_documents(filter_complex_metadata(docs), embeddings)
    chat_id = generate_random_string(10)

    # Prepara los retriever para Hybrid-Search
    # Metadata tiene que ser del mismo largo que los chunks
    bm25_retriever_metadatas = [
        {"source": "BM25Retriever", **meta} for meta in metadatas
    ]  # Combine with existing metadata
    bm25_retriever = BM25Retriever.from_texts(
        texts=splitted_text, metadatas=bm25_retriever_metadatas, ids=uuids
    )
    bm25_retriever.k = config["ragSearchK"]

    faiss_metadatas = [{"source": "FAISS", **meta} for meta in metadatas]
    faiss_vectorstore = FAISS.from_texts(
        texts=splitted_text, embedding=embeddings, metadatas=faiss_metadatas, ids=uuids
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
    # Create a retriever from the databases
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


def get_hybrid_retriever_with_tags():
    global bm25_retriever
    global faiss_vectorstore
    config = load_config()

    class CustomHybridRetriever(BaseRetriever):
        def _get_relevant_documents(
            self, query: str, *, run_manager: CallbackManagerForRetrieverRun
        ) -> List[Document]:
            query_tags = generate_tags("query", query)

            # Looks like we cant implement metadata search inside the retrievers
            # Perform BM25 search
            bm25_results = bm25_retriever.invoke(query)

            # Perform vector search
            faiss_results = faiss_vectorstore.similarity_search(
                query, k=config["ragSearchK"]
            )

            # search by keywords "tags" in chroma
            db = get_db()
            keyword_results = db.similarity_search(
                query,
                filter={
                    "$or": [
                        {
                            "tag_1": {"$in": query_tags},
                        },
                        {"tag_2": {"$in": query_tags}},
                        {"tag_3": {"$in": query_tags}},
                    ]
                },
            )
            # Combine results
            all_results = bm25_results + faiss_results + keyword_results

            # Deduplicate results based on a unique identifier
            seen_ids = set()
            unique_results = []
            for doc in all_results:
                if (
                    doc.metadata["id"] not in seen_ids
                ):  # Replace `id` with the appropriate unique attribute
                    seen_ids.add(doc.metadata["id"])
                    unique_results.append(doc)

            # Filter results based on tag matching
            # como buscamos many-to-many, la DB no puede hacer esta pega la hacemos nosotros
            # filtered_results = [
            #     doc
            #     for doc in unique_results
            #     if any(tag in doc.metadata.get("tags", []) for tag in query_tags)
            # ]

            # If no documents match the tags, return all results
            # return filtered_results if filtered_results else unique_results
            return unique_results

    # Rerank and return n documents, base retriever have 3 retrievers that each return n docs, select n most relevant
    compressor = FlashrankRerank(top_n=config["ragSearchK"])
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor, base_retriever=CustomHybridRetriever()
    )

    # return CustomHybridRetriever()
    return compression_retriever


def query_rag(query, verbose=False):
    global chat_id
    config = load_config()
    # set_debug(True)
    # retriever = get_retriever()

    if config["useTags"] == "si":
        retriever = get_hybrid_retriever_with_tags()
    else:
        retriever = get_hybrid_retriever()

    rag_llm = None

    # Esto es solo para Debug
    # retriever_test = get_hybrid_retriever_with_tags()
    # relevant_docs = retriever_test.invoke(query)
    # for i, doc in enumerate(relevant_docs, 1):
    #     print(f"Document {i}:\n {doc.page_content}\n")
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
    contextualize_q_system_prompt = "Tu tarea es exclusivamente reformular la siguiente pregunta para que sea entendida sin contexto adicional. Bajo ninguna circunstancia debes proporcionar una respuesta o explicación. Si la pregunta ya es clara y no necesita reformulación, devuélvela tal como está. Solo realiza la reformulación, sin añadir contenido extra."

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
