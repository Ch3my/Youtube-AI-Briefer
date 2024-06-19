"""
# Instalar Dependencias #

Tambien es necesario setear OPENAI_API_KEY en el ambiente.

!pip install youtube-transcript-api
!pip install --upgrade openai
"""

from youtube_transcript_api import YouTubeTranscriptApi
from pprint import pprint

from openai import OpenAI

client = OpenAI()

YT_VIDEO_ID = "qp1RBrVnBnk"

# Nos aseguramos traer el modelo, ayuda a no tener que
# El transcript llega un JSON con cada dialogo como subtitulos, lo juntamos todo en un solo string
chunks = YouTubeTranscriptApi.get_transcript(YT_VIDEO_ID, languages=["es", "en"])
transcript = []

for i in chunks:
  transcript.append(i["text"])

transcript = " ".join(transcript)
print(transcript)


def split_text_into_sections_by_number_of_words(text, words_per_section, overlap):
    words = text.split()

    sections = []
    i = 0

    while i < len(words):
        # Define the start and end indices for the current section
        start_index = i
        end_index = i + words_per_section

        # Extract the current section of words
        section = " ".join(words[start_index:end_index])
        sections.append(section)

        # Move the index forward by the number of words per section minus the overlap
        i += words_per_section - overlap

    return sections

trascript_sections = split_text_into_sections_by_number_of_words(transcript, 1500, 100)
notes = []

for section in trascript_sections:
  completion = client.chat.completions.create(
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


print("\n =========== Estas son las notas de cada seccion ==================== \n")
print("\n ====== seccion =========== \n".join(notes))

notas_unidas = "\n".join(notes)

response = client.chat.completions.create(
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
        {notas_unidas}
        """
      }
    ]
  )

print(response.choices[0].message.content)