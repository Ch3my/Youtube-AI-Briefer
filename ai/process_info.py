# Aqui debemos cargar lanchain y crear las funciones que
# Condensa el transcript, quiza usando algo de langchain para
# split el text

# Lanchain puede usar OPENAI o ANTHROPIC solito, nos evita tener que
# crear archivos diferentes, de hecho es la razon por la que usamos LANGCHAIN

# Quiza Crear resume y condensa en archivos separados?

import threading
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ai.rag_functions import build_rag
from functions.get_transcript import get_transcript
from functions.load_config import load_config
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from functions.logger import log_message
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

    # A penas tenemos el Transcript enviamos a crear el Rag, asi cuando probablemente terminenos el RAG
    # antes de que termine el procesamiento. La coma es necesaria, sino piensa que cada caracter es un argumento
    rag_thread = threading.Thread(target=build_rag, args=(transcript,))
    # A daemon thread is a thread that doesn’t prevent the program from exiting. 
    # If the program ends or all non-daemon threads finish execution, any remaining daemon threads are stopped.
    rag_thread.setDaemon(True)
    rag_thread.start()
    
    formatted_length_fstring = f"{len(transcript):,}"
    set_feedback_msg(f"Transcript obtenido ({formatted_length_fstring} caracteres)")

    try:
        if "claude" in config["resumeModel"]:
            resume_model = ChatAnthropic(model=config["resumeModel"], max_tokens=2048)

        if "gpt" in config["resumeModel"]:
            resume_model = ChatOpenAI(model=config["resumeModel"])

        if "claude" in config["condensaModel"]:
            # max_tokens por defecto es 1024, si intenta generar una respuesta mas grande simplemente
            # la trunca, el numero maximo depende del modelo
            condensa_model = ChatAnthropic(
                model=config["condensaModel"], max_tokens=3072
            )

        if "gpt" in config["condensaModel"]:
            # Por defecto max_tokens en ChatOpenAI is None, supongo que no tiene limite
            condensa_model = ChatOpenAI(model=config["condensaModel"])

    except Exception as e:
        callback("Error al configurar los modelos, quiza falta una API_KEY")
        print("Error al configurar los modelos, quiza falta una API_KEY")
        print(e)
        return

    resume_template = """
        Instrucciones para la toma de notas detalladas:

        1. Lee el texto proporcionado minuciosamente, asegurándote de comprender a fondo su contenido.
        
        2. Identifica y anota todas las ideas principales, conceptos clave, argumentos centrales y conclusiones importantes presentes en el texto.
        
        4. Para cada idea principal, escribe una prosa incluyendo (pero no te limites a): Explicacion detallada y Datos o estadísticas o cifras relevantes

        5. Respeta la estructura original del texto, incluyendo:
            - La progresión lógica de las ideas
            - Conexiones entre diferentes secciones o conceptos
            - Cualquier jerarquía o categorización presente

        6. Anota cualquier terminología especializada, definiciones o conceptos técnicos introducidos en el texto, proporcionando explicaciones concisas.

        7. Identifica y registra:
            - Cualquier pregunta planteada y sus respuestas
            - Problemas presentados y sus soluciones propuestas
            - Hipótesis formuladas y evidencias que las respaldan

        8. Si el texto discute múltiples perspectivas o argumentos contrastantes, asegúrate de capturar todas ellas de manera equilibrada.

        9. Mantén la objetividad en todo momento. No agregues interpretaciones personales, opiniones o información que no esté presente en el texto original.

        10. Responde siempre en español, manteniendo la terminología original si está en otro idioma, pero proporcionando traducciones o explicaciones cuando sea necesario.

        11. Sé lo más exhaustivo y detallado posible en tus notas, sin omitir ningún aspecto significativo del texto.

        Recuerda. Tu objetivo es crear un conjunto de notas que sean lo suficientemente detalladas y completas como para que alguien que las lea pueda obtener una comprensión profunda y exhaustiva del texto original sin necesidad de referirse a él directamente.
        
        El Texto:
        {chunk}"""

    prompt_template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Eres un agente que se encarga de tomar notas detalladas sobre el texto en español. Los conceptos deben presentarse en forma detallada incluyendo una explicacion de cada idea.",
            ),
            ("user", resume_template),
        ]
    )

    # Crea una chain, esta la ejecutamos en un loop y no en un chain automatico
    note_chain = prompt_template | resume_model | parser

    # Se supone que RecursiveCharacterTextSplitter corta en parrafos o oraciones, para no romper el sentido del texto
    # a la vez que intenta mantenerse dentro de los limites establecidos
    # El chunk_size es en tokens por defecto
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=config["resumeChunkSize"], chunk_overlap=0
    )
    chunks = text_splitter.split_text(transcript)

    set_feedback_msg(f"Generando notas ({len(chunks)} secciones)")

    try:
        notes = [note_chain.invoke({"chunk": chunk}) for chunk in chunks]
    except Exception as e:
        callback("Error al conectarse con AI")
        log_message(f"Error durante el procesamiento de chunks: {e}")
        return

    set_feedback_msg("Generando documento final")

    notes_join = "\n\n".join(notes)

    condensa_prompt = """
        1. Escribe como Nia, eres mi asistente, escribe como si me estuvieras entregando el informe en persona, no es necesario que te presentes ya nos conocemos. Tu trato debe ser cercano pero respetuoso.
        2. Redacta un documento coherente y exhaustivo en español, utilizando formato Markdown, que incorpore toda la información de las notas. El documento debe incluir:

        ## Al escribir utiliza esta estructura, si el texto no incluye informacion sobre alguna seccion simplemente no la escribas 
            - Un breve título principal que refleje el tema general.
            - Un abstracto que presente el tema general y los puntos principales que se cubrirán.
            - Subtítulos para cada sección principal, utilizando los niveles de encabezado apropiados (##, ###, ####, etc.).
            - Secciones de contenido principal que desarrollen cada tema en detalle.

        ## Contenido
            - Explica cada idea y concepto con el máximo detalle posible, aprovechando toda la información disponible en las notas.
            - Presenta cualquier argumento, contraargumento, o perspectivas múltiples que se hayan registrado en las notas.
            - Menciona cualquier limitación, advertencia o área de incertidumbre que se haya anotado.
            - Incluye todos los ejemplos y datos estadísticos presentes en las notas, utilizando el formato apropiado (listas para enumeraciones, etc.).
            - Incorpora cualquier definición, terminología especializada o conceptos técnicos mencionados en las notas, proporcionando explicaciones claras.

        3. Asegúrate de que el documento fluya lógicamente de un tema a otro, proporcionando transiciones suaves entre secciones.

        4. Mantén un tono objetivo y académico en todo el documento, evitando opiniones personales o información no presente en las notas originales.

        5. Revisa el documento final para garantizar que:
            - Se ha incluido toda la información relevante de las notas.
            - El formato Markdown se ha aplicado correctamente y consistentemente.
            - El documento es coherente, bien estructurado y fácil de leer.
            - No hay repeticiones innecesarias de información.

        Recuerda: Tu objetivo es crear un documento exhaustivo y bien estructurado que capture toda la riqueza y detalle de las notas originales, presentándolo de una manera coherente y fácil de entender para el lector.

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

    try:
        final_document = condensa_chain.invoke({"notes": notes_join})
    except Exception as e:
        callback("Error al conectarse con AI")
        log_message(f"Error durante el procesamiento Documento Final: {e}")
        return

    # Display result in the main thread
    callback("Procesamiento completado")
    MAIN_WINDOW.after(0, display_result, transcript, final_document, notes_join)
