import tkinter as tk
import pyperclip
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
from screens.config_screen import config_screen
from ai.process_info import fn

# Define a callback function to update the UI after thread completes
def update_ui(message):
    button.config(state=tk.NORMAL)
    if message is not None:
        set_feedback_msg(message)

def on_button_click():
    url = entry.get()
    if url == "":
        set_feedback_msg("Por favor ingresa un link")
        button.config(state=tk.NORMAL)
        return

    set_feedback_msg("Estamos procesando el Video :D")
    button.config(state=tk.DISABLED)
    threading.Thread(target=fn, args=(url, update_ui)).start()

def on_update_window(event):
    feedback_label.config(wraplength=MAIN_WINDOW.winfo_width() - 50)

def paste_from_clipboard():
    clipboard_content = pyperclip.paste()
    entry.delete(0, tk.END)
    entry.insert(0, clipboard_content)

def on_enter_key(event):
    on_button_click()

# Create the main window
MAIN_WINDOW.title("Youtube AI Briefer")
MAIN_WINDOW.geometry("450x250")  # Set the size of the window

# Configure the main window with dark theme
MAIN_WINDOW.configure(bg=BG_COLOR, padx=20, pady=20)

# Create a label for displaying messages to the user
feedback_label = tk.Label(
    MAIN_WINDOW,
    text=get_feedback_msg(),
    font=("Consolas", 14),
    bg=BG_COLOR,
    fg=FG_COLOR,
    wraplength=370,
    justify="left",
)
feedback_label.pack(fill="x", pady=(0, 10))  # Add padding below the message label
# globals verifica si tiene algo llamado feedback_label, para hacerle un update, por eso debemos pasarlo
globals_instance.feedback_label = feedback_label

separator2 = tk.Frame(MAIN_WINDOW, bg="gray", height=1, bd=0)
separator2.pack(fill="x")
separator2.pack(pady=(10, 10))  # Add padding below the message label

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
    font=("Consolas", 12),
    bg=ENTRY_BG_COLOR,
    fg=ENTRY_FG_COLOR,
    insertbackground=FG_COLOR,
    bd=0,
)
entry.pack(pady=(0, 10), fill="x", ipady=5, ipadx=5)
entry.bind("<Return>", on_enter_key)  # Bind Enter key to on_button_click

frame = tk.Frame(MAIN_WINDOW, bg=BG_COLOR)
frame.pack(fill=tk.X)

grid_frame = tk.Frame(frame, bg=BG_COLOR)
grid_frame.pack(fill=tk.X, expand=True)

config_btn = tk.Button(
    grid_frame,
    text="⚙",
    command=config_screen,
    height=1,
    bg=BTN_BG_COLOR,
    fg=FG_COLOR,
    font=("Consolas", 16),
    bd=0,
)
config_btn.pack(side=tk.LEFT, padx=(0, 10))

paste_btn = tk.Button(
    grid_frame,
    text="📋",
    command=paste_from_clipboard,
    height=1,
    bg=BTN_BG_COLOR,
    fg=FG_COLOR,
    font=("Consolas", 16),
    bd=0,
)
paste_btn.pack(side=tk.LEFT, padx=(0, 10))

button = tk.Button(
    grid_frame,
    text="Procesar",
    command=on_button_click,
    height=1,
    bg=BTN_BG_COLOR,
    fg=FG_COLOR,
    font=("Consolas", 16),
    bd=0,
)
button.pack(side=tk.LEFT, fill=tk.X, expand=True)

MAIN_WINDOW.bind("<Configure>", on_update_window)
# Run the application
MAIN_WINDOW.mainloop()