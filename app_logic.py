from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
from split_text import split_text_into_sections_by_number_of_words
from get_video_id import get_video_id
from globals import OPENAI_CLIENT, set_feedback_msg

def get_transcript(url):
    YT_VIDEO_ID = get_video_id(url)
    if YT_VIDEO_ID is None:
        return None

    # Nos aseguramos traer el modelo, ayuda a no tener que
    # El transcript llega un JSON con cada dialogo como subtitulos, lo juntamos todo en un solo string
    chunks = []
    try:
        # Your code that might raise the TranscriptsDisabled exception
        chunks = YouTubeTranscriptApi.get_transcript(YT_VIDEO_ID, languages=["es", "en"])
    except TranscriptsDisabled as e:
        print("Caught TranscriptsDisabled exception:", e)
        set_feedback_msg("La transcripcion esta desactivada para este video :(")
        return None

    transcript = []
    for i in chunks:
        transcript.append(i["text"])

    transcript = " ".join(transcript)
    return transcript

def resume_transcript(transcript):
    trascript_sections = split_text_into_sections_by_number_of_words(transcript, 1500, 100)
    notes = []

    for section in trascript_sections:
        completion = OPENAI_CLIENT.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
            {"role": "system", "content": "Eres un agente que se encarga de entregar un Estudio Detallado sobre el texto en español. Los conceptos deben presentarse en forma detallada incluyendo una explicacion de cada idea."},
            {"role": "user", "content":
                f"""
                Instrucciones:
                Lee cuidadosamente el texto para entender contenido
                Escribe todas las ideas importantes, incluye todos los detalles necesarios
                Centrate en el contenido, no des recomendaciones ni ideas que no se incluyen en el texto original
                Responde siempre en español

                Texto:
                {section}
                """
            }
            ]
        )
        notes.append(completion.choices[0].message.content)
    notas_unidas = "\n".join(notes)
    return notas_unidas

def condensa_transcript(notes):
    # Toma las notas y las condensa en un solo documento
    response = OPENAI_CLIENT.chat.completions.create(
        model="gpt-4o",
        messages=[
        {"role": "system", "content": "Eres un agente que se encarga de organizar las notas en un solo documento"},
        {"role": "user", "content":
            f"""
            Instrucciones:
            Incorpora las notas en un solo texto coherente, debes incluir el maximo nivel de informacion posible.
            Explica cada idea con detalle aprovechando al maximo el contenido de las notas
            Utiliza la mayor cantidad de detalles de las notas que se entregaron
            Escribe en español y utiliza formato markdown

            Las siguientes notas fueron seleccionadas basadas en su relevancia e importancia

            Las Notas:
            {notes}
            """
        }
        ]
    )

    return response.choices[0].message.content