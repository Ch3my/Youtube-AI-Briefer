from app_logic import get_transcript, resume_transcript, condensa_transcript
from tkinter import messagebox
from globals import MAIN_WINDOW
from display_result import display_result

def fetch_and_display_transcript(url, callback):
    transcript = get_transcript(url)

    if transcript is None:
        # messagebox.showinfo("Input", "No se logró obtener el transcript :(")
        return

    analisis = resume_transcript(transcript)
    condensa = condensa_transcript(analisis)
    
    callback("Procesamiento completado")

    # Display result in the main thread
    MAIN_WINDOW.after(0, display_result, condensa)