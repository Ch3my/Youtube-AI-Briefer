from ai.whisper_transcript import detect_language_and_transcribe
from functions.get_video_id import get_video_id
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from globals import set_feedback_msg
from functions.load_config import load_config
from tkinter import messagebox
import pygame

def ask_user_confirmation():
    pygame.mixer.init()
    pygame.mixer.music.load("assets/finish-sound.mp3")
    pygame.mixer.music.play()
    return messagebox.askyesno("Confirmar uso de Whisper", "¿Desea utilizar Whisper para transcribir el audio? Esto puede tomar varios minutos.")

def use_whisper(url):
    config = load_config()

    if config["useWhisper"] == "no":
        set_feedback_msg("No se pudo conseguir la transcripcion. Whisper esta Desactivado")
        return None
    
    if not ask_user_confirmation():
        set_feedback_msg("Transcripción con Whisper cancelada por el usuario")
        return None

    set_feedback_msg("Utilizando Whisper para obtener un transcript")
    try:
        transcript = detect_language_and_transcribe(url)
    except Exception as e: 
        print(e)
        set_feedback_msg("Error al intentar conseguir audio con Whisper")
        return None
    return transcript

def get_transcript(url):
    YT_VIDEO_ID = get_video_id(url)
    if YT_VIDEO_ID is None:
        return None

    # Nos aseguramos traer el modelo, ayuda a no tener que
    # El transcript llega un JSON con cada dialogo como subtitulos, lo juntamos todo en un solo string
    chunks = []
    transcript = ""
    try:
        # Your code that might raise the TranscriptsDisabled exception
        chunks = YouTubeTranscriptApi.get_transcript(YT_VIDEO_ID, languages=["es", "en", "en-GB"])
        transcript = []
        for i in chunks:
            transcript.append(i["text"])
        transcript = "".join(transcript)

    except TranscriptsDisabled as e:
        print("Caught TranscriptsDisabled exception:", e)
        set_feedback_msg("La transcripcion esta desactivada para este video")
        transcript = use_whisper(url)
    except NoTranscriptFound as e:
        print("Caught NoTranscriptFound exception:", e)
        set_feedback_msg("No existe un transcript en los idiomas aceptados")
        transcript = use_whisper(url)

    return transcript