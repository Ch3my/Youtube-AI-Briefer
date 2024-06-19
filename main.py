import tkinter as tk
from globals import (
    MAIN_WINDOW,
    BG_COLOR,
    FG_COLOR,
    BTN_BG_COLOR,
    ENTRY_BG_COLOR,
    ENTRY_FG_COLOR,
    set_feedback_msg,
    get_feedback_msg,
    globals_instance,
)
import threading
from fetch_and_display_transcript import fetch_and_display_transcript

# Define a callback function to update the UI after thread completes
def update_ui(message):
    button.config(state=tk.NORMAL)
    set_feedback_msg(message)


def on_button_click():
    # Declaro que la variable es global en realidad
    global is_button_enabled
    url = entry.get()
    if url == "":
        set_feedback_msg("Por favor ingresa un link")
        return

    set_feedback_msg("Estamos procesando el Video :D")
    button.config(state=tk.DISABLED)
    threading.Thread(target=fetch_and_display_transcript, args=(url, update_ui)).start()


# Create the main window
MAIN_WINDOW.title("Youtube AI Briefer")
MAIN_WINDOW.geometry("450x350")  # Set the size of the window

# Configure the main window with dark theme
MAIN_WINDOW.configure(bg=BG_COLOR)

# Create a label for displaying messages to the user
feedback_label = tk.Label(
    MAIN_WINDOW,
    text=get_feedback_msg(),
    font=("Consolas", 14),
    bg=BG_COLOR,
    fg=FG_COLOR,
)
feedback_label.pack(pady=(0, 10))  # Add padding below the message label
# globals verifica si tiene algo llamado feedback_label, para hacerle un update, por eso debemos pasarlo
globals_instance.feedback_label = feedback_label

# Separator object
separator = tk.Frame(MAIN_WINDOW, bg="gray", height=1, bd=0)
separator.pack(fill="x")
separator.pack(pady=(0, 10))  # Add padding below the message label

info = tk.Label(
    MAIN_WINDOW,
    text="Transcribe un video de Youtube y lo procesa con IA para obtener un resumen completo del contenido. Para funcionar debes setear OPENAI_API_KEY en el Entorno",
    font=("Consolas", 12),
    bg=BG_COLOR,
    fg=FG_COLOR,
    wraplength=370,
    justify="left",
)
info.pack(pady=(0, 10), anchor="w")

separator2 = tk.Frame(MAIN_WINDOW, bg="gray", height=1, bd=0)
separator2.pack(fill="x")
separator2.pack(pady=(0, 10))  # Add padding below the message label

message_label = tk.Label(
    MAIN_WINDOW,
    text="Ingresa el link de Youtube",
    font=("Consolas", 14),
    bg=BG_COLOR,
    fg=FG_COLOR,
    justify="left",
)
message_label.pack(pady=(0, 5), anchor="w")

# Create an input field with dark theme
entry = tk.Entry(
    MAIN_WINDOW,
    font=("Consolas", 14),
    bg=ENTRY_BG_COLOR,
    fg=ENTRY_FG_COLOR,
    insertbackground=FG_COLOR,
    bd=0,
)
entry.pack(pady=(0, 20), fill="x", ipady=5, ipadx=5)  

# Create a big button with dark theme
button = tk.Button(
    MAIN_WINDOW,
    text="Procesar",
    command=on_button_click,
    height=1,
    bg=BTN_BG_COLOR,
    fg=FG_COLOR,
    font=("Consolas", 16),
)
button.pack(fill="x")

# Add padding around the entire window
padding = 20
MAIN_WINDOW.configure(padx=padding, pady=padding)

# Run the application
MAIN_WINDOW.mainloop()
