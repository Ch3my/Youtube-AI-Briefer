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

# NOTE. Pseudo-Singleton, not private constructor

# Global variable to store the database
_db = None
config = load_config()

def get_embeddings():
    model_name = "sentence-transformers/all-mpnet-base-v2"
    model_kwargs = {"device": "cpu"}
    encode_kwargs = {"normalize_embeddings": False}
    return HuggingFaceEmbeddings(
        model_name=model_name, model_kwargs=model_kwargs, encode_kwargs=encode_kwargs
    )


def build_rag(transcript):
    global _db
    # split it into chunks. TODO chunk_size en Config?
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=0)
    docs = [Document(page_content=x) for x in text_splitter.split_text(transcript)]

    embeddings = get_embeddings()

    # load it into Chroma
    _db = Chroma.from_documents(docs, embeddings, persist_directory="./vector-db")
    return _db


def get_db():
    global _db
    if _db is None:
        # If no db is loaded, load the existing one
        embeddings = get_embeddings()
        _db = Chroma(persist_directory="./vector-db", embedding_function=embeddings)
    return _db


def get_retriever():
    db = get_db()
    # Create a retriever from the database
    return db.as_retriever(
        search_type=config["ragSearchType"], search_kwargs={"k": config["ragSearchK"]}
    )


def query_rag(query, verbose=False):
    retriever = get_retriever()
    rag_llm = None

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
            ("human", "{input}"),
        ]
    )

    # Esto es algo que viene en langchain: https://python.langchain.com/v0.2/docs/tutorials/rag/#built-in-chains
    # pero funciona bien, no tenemos que crear a mano una chain (creo)
    question_answer_chain = create_stuff_documents_chain(rag_llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    response = rag_chain.invoke({"input": query})
    return response["answer"]


# Example usage:
# transcript = "Your transcript text here"
# build_rag(transcript)  # Only need to call this once to create/update the database
# query_rag("de que trata el texto?")
# query_rag("otra pregunta")  # Will reuse the existing database
