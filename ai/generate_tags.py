from functions.load_config import load_config
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

def generate_tags(target="search", text=""):
    """
    target=search/query, que tipo de tags generara basado en el uso que le daremos
        search se usa cuando generamos tags que se iran a la vectorDB
        query es cuando hacemos una pregunta y queremos extraer el
    txt= es el texto del cual generaremos los tags
    """
    config = load_config()
    resume_model = None
    
    try:
        if "claude" in config["resumeModel"]:
            resume_model = ChatAnthropic(model=config["resumeModel"], max_tokens=2048)
        if "gpt" in config["resumeModel"]:
            resume_model = ChatOpenAI(model=config["resumeModel"])
    except Exception as e:
        # TODO. Handle Error
        return

    prompt_template = None
    system_prompt = "Tu tarea es procesar el texto que los usuarios te proporcionen y extraer las keywords más relevantes, ***las keywords debes entregarlas separadas por coma***. Estas keywords deben ser seleccionadas con el objetivo de facilitar la búsqueda de información en bases de datos o sistemas de información. Debes asegurarte de identificar las palabras clave que mejor representen el núcleo de la pregunta, enfocándote en los términos que son fundamentales para entender el contexto y los conceptos clave. Evita palabras irrelevantes o demasiado generales, y prioriza los términos más específicos y útiles para la búsqueda."
    
    if target == "search":
        base_prompt = """
        "Dado el siguiente texto, extrae las ***keywords*** más relevantes. Estas keywords serán utilizadas para filtrar y realizar búsquedas eficientes dentro de un conjunto de datos dividido en chunks. Por lo tanto, asegúrate de seleccionar las palabras clave que representen de forma precisa los conceptos más importantes y únicos del texto. Las keywords deben estar relacionadas con los temas principales y ser útiles para identificar el contenido esencial del texto."
        Texto:
        {text}
        """
        prompt_template = ChatPromptTemplate.from_messages(
            [("system", system_prompt), ("user", base_prompt)]
        )
    if target == "query":
        base_prompt = """
        "Dada la siguiente pregunta, extrae las ***keywords*** más importantes. Estas keywords serán usadas para realizar una búsqueda precisa en una base de datos o sistema de información. Por lo tanto, selecciona las palabras clave que mejor representen el núcleo de la pregunta y ayuden a identificar la información relevante."
        Pregunta:
        {text}
        """
        prompt_template = ChatPromptTemplate.from_messages(
            [("system", system_prompt), ("user", base_prompt)]
        )

    chain = prompt_template | resume_model | StrOutputParser()
    result = chain.invoke({"text": text})
    # trim each element
    result_array = [element.strip() for element in result.split(",")]

    return result_array