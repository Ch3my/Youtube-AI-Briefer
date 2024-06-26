import sys
import os
import json
import tkinter as tk
from tkinter import ttk

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from functions.load_config import load_config
from globals import MAIN_WINDOW, BG_COLOR, BTN_BG_COLOR, FG_COLOR, CONFIG_FILE, AVAILABLE_MODELS

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def config_screen():
    config = load_config()

    def on_update_window(event):
        info.config(wraplength=config_window.winfo_width() - 50)
        model_info.config(wraplength=config_window.winfo_width() - 50)

    def on_save():
        config["resumeModel"] = resume_model_var.get()
        config["condensaModel"] = condensa_model_var.get()
        config["resumeChunkSize"] = int(chunk_size_var.get())
        save_config(config)
        config_window.destroy()

    config_window = tk.Toplevel(MAIN_WINDOW)
    config_window.title("Config")
    config_window.geometry("500x600")  # Increased height to accommodate new input
    config_window.configure(bg=BG_COLOR)

    content_frame = tk.Frame(config_window, bg=BG_COLOR, padx=20, pady=20)
    content_frame.pack(expand=True, fill=tk.BOTH)

    info = tk.Label(
        content_frame,
        text="Transcribe un video de Youtube y lo procesa con IA para obtener un resumen completo del contenido.",
        font=("Consolas", 14),
        bg=BG_COLOR,
        fg=FG_COLOR,
        wraplength=370,
        justify="left",
    )
    info.grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky=tk.W)
    api_key_info = tk.Label(
        content_frame,
        text="Para funcionar debes setear OPENAI_API_KEY y/o ANTHROPIC_API_KEY en el Entorno segun la configuración que se muestra aqui",
        font=("Consolas", 14),
        bg=BG_COLOR,
        fg=FG_COLOR,
        wraplength=370,
        justify="left",
    )
    api_key_info.grid(row=1, column=0, columnspan=2, pady=(0, 20), sticky=tk.W)

    model_info = tk.Label(
        content_frame,
        text="Selecciona el modelo para cada parte del proceso:",
        font=("Consolas", 14),
        bg=BG_COLOR,
        fg=FG_COLOR,
        wraplength=370,
        justify="left",
    )
    model_info.grid(row=2, column=0, columnspan=2, pady=(0, 20), sticky=tk.W)

    # Resume Model Selection
    resume_label = tk.Label(content_frame, text="Resume Model:", font=("Consolas", 14), bg=BG_COLOR, fg=FG_COLOR)
    resume_label.grid(row=3, column=0, sticky="w", padx=(0, 10), pady=5)

    resume_model_var = tk.StringVar(value=config["resumeModel"])
    resume_model_combo = ttk.Combobox(content_frame, textvariable=resume_model_var, values=AVAILABLE_MODELS, font=("Consolas", 14), height=10)
    resume_model_combo.grid(row=3, column=1, sticky="ew", pady=5)

    # Resume Chunk Size Input
    chunk_size_label = tk.Label(content_frame, text="Resume Chunk Size:", font=("Consolas", 14), bg=BG_COLOR, fg=FG_COLOR)
    chunk_size_label.grid(row=4, column=0, sticky="w", padx=(0, 10), pady=5)

    chunk_size_var = tk.StringVar(value=str(config.get("resumeChunkSize", 1000)))  # Default to 1000 if not set
    chunk_size_entry = ttk.Entry(content_frame, textvariable=chunk_size_var, font=("Consolas", 14))
    chunk_size_entry.grid(row=4, column=1, sticky="ew", pady=5)

    # Condensa Model Selection
    condensa_label = tk.Label(content_frame, text="Condensa Model:", font=("Consolas", 14), bg=BG_COLOR, fg=FG_COLOR)
    condensa_label.grid(row=5, column=0, sticky="w", padx=(0, 10), pady=5)

    condensa_model_var = tk.StringVar(value=config["condensaModel"])
    condensa_model_combo = ttk.Combobox(content_frame, textvariable=condensa_model_var, values=AVAILABLE_MODELS, font=("Consolas", 14), height=10)
    condensa_model_combo.grid(row=5, column=1, sticky="ew", pady=5)



    # Save Button
    save_button = tk.Button(
        content_frame,
        text="Guardar",
        command=on_save,
        bg=BTN_BG_COLOR,
        fg=FG_COLOR,
        font=("Consolas", 14),
        bd=0
    )
    save_button.grid(row=6, column=0, columnspan=2, pady=20, sticky="we")

    # Configure grid weights
    content_frame.columnconfigure(1, weight=1)

    config_window.bind("<Configure>", on_update_window)

    return config_window