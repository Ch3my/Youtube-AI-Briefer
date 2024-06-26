# Aqui debemos cargar lanchain y crear las funciones que
# Condensa el transcript, quiza usando algo de langchain para
# split el text

# Lanchain puede usar OPENAI o ÄNTHROPIC solito, nos evita tener que
# crear archivos diferentes, de hecho es la razon por la que usamos LANGCHAIN

# Quiza Crear resume y condensa en archivos separados?

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from functions.get_transcript import get_transcript
from functions.load_config import load_config
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from globals import MAIN_WINDOW, set_feedback_msg
from screens.display_result import display_result

def fn(url, callback):
    config = load_config()
    parser = StrOutputParser()
    resume_model = None
    condensa_model = None

    transcript = get_transcript(url)

    if transcript is None:
        callback(None)
        return
    try:
        if "claude" in config["resumeModel"]:
            resume_model = ChatAnthropic(model=config["resumeModel"])

        if "gpt" in config["resumeModel"]:
            resume_model = ChatOpenAI(model=config["resumeModel"])

        if "claude" in config["condensaModel"]:
            condensa_model = ChatAnthropic(model=config["condensaModel"])

        if "gpt" in config["condensaModel"]:
            condensa_model = ChatOpenAI(model=config["condensaModel"])
    except Exception as e:
        set_feedback_msg("Error al configurar los modelos, quiza falta una API_KEY")
        print("Error al configurar los modelos, quiza falta una API_KEY")
        print(e)
        return

    resume_template = """
        Instrucciones:
        Lee cuidadosamente el texto para entender contenido
        Escribe todas las ideas importantes, incluye todos los detalles necesarios
        Centrate en el contenido, no des recomendaciones ni ideas que no se incluyen en el texto original
        Responde siempre en español 
        
        El Texto:
        {chunk}"""

    prompt_template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Eres un agente que se encarga de entregar un Estudio Detallado sobre el texto en español. Los conceptos deben presentarse en forma detallada incluyendo una explicacion de cada idea.",
            ),
            ("user", resume_template),
        ]
    )

    # Crea una chain, esta la ejecutamos en un loop y no en un chain automatico
    note_chain = prompt_template | resume_model | parser

    # Se supone que RecursiveCharacterTextSplitter corta en parrafos o oraciones, para no romper el sentido del texto
    # a la vez que intenta mantenerse dentro de los limites establecidos
    # El chunk_size es en tokens por defecto
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=config["resumeChunkSize"], chunk_overlap=0)
    chunks = text_splitter.split_text(transcript)

    notes = [note_chain.invoke({"chunk": chunk}) for chunk in chunks]

    condensa_prompt = """
        Instrucciones:
        Incorpora las notas en un solo texto coherente, debes incluir el maximo nivel de informacion posible.
        Explica cada idea con detalle aprovechando al maximo el contenido de las notas
        Utiliza la mayor cantidad de detalles de las notas que se entregaron
        Escribe en español y utiliza formato markdown

        Las Notas:
        {notes}
        """

    condensa_template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Eres un agente que se encarga de entregar un Estudio Detallado sobre el texto en español. Los conceptos deben presentarse en forma detallada incluyendo una explicacion de cada idea.",
            ),
            ("user", condensa_prompt),
        ]
    )

    # Ejecuta
    condensa_chain = condensa_template | condensa_model | StrOutputParser()
    final_document = condensa_chain.invoke({"notes": "\n\n".join(notes)})

    # Display result in the main thread
    callback("Procesamiento completado")
    MAIN_WINDOW.after(0, display_result, transcript, final_document)
