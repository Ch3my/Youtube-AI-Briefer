import sys
import os
import json
import threading
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
        api_key_info.config(wraplength=config_window.winfo_width() - 50)
        model_info.config(wraplength=config_window.winfo_width() - 50)

    def on_save():
        config["resumeModel"] = resume_model_var.get()
        config["condensaModel"] = condensa_model_var.get()
        config["resumeChunkSize"] = int(chunk_size_var.get())
        config["ragModel"] = rag_model_var.get()
        config["ragSearchType"] = rag_search_type_var.get()
        config["ragSearchK"] = int(rag_search_k_var.get())
        config["ragChunkSize"] = int(rag_chunk_size_var.get())  # New line
        save_config(config)
        config_window.destroy()
    # For Debug
    # mythreads = threading.enumerate()
    
    config_window = tk.Toplevel(MAIN_WINDOW)
    config_window.iconbitmap('assets/favicon.ico')
    config_window.title("Config")
    config_window.geometry("600x650")  # Increased height to accommodate new input
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

    chunk_size_var = tk.StringVar(value=str(config.get("resumeChunkSize", 5000)))
    chunk_size_entry = ttk.Entry(content_frame, textvariable=chunk_size_var, font=("Consolas", 14))
    chunk_size_entry.grid(row=4, column=1, sticky="ew", pady=5)

    # Condensa Model Selection
    condensa_label = tk.Label(content_frame, text="Condensa Model:", font=("Consolas", 14), bg=BG_COLOR, fg=FG_COLOR)
    condensa_label.grid(row=5, column=0, sticky="w", padx=(0, 10), pady=5)

    condensa_model_var = tk.StringVar(value=config["condensaModel"])
    condensa_model_combo = ttk.Combobox(content_frame, textvariable=condensa_model_var, values=AVAILABLE_MODELS, font=("Consolas", 14), height=10)
    condensa_model_combo.grid(row=5, column=1, sticky="ew", pady=5)

    # RAG Model Selection
    rag_label = tk.Label(content_frame, text="RAG Model:", font=("Consolas", 14), bg=BG_COLOR, fg=FG_COLOR)
    rag_label.grid(row=6, column=0, sticky="w", padx=(0, 10), pady=5)

    rag_model_var = tk.StringVar(value=config.get("ragModel", AVAILABLE_MODELS[0]))
    rag_model_combo = ttk.Combobox(content_frame, textvariable=rag_model_var, values=AVAILABLE_MODELS, font=("Consolas", 14), height=10)
    rag_model_combo.grid(row=6, column=1, sticky="ew", pady=5)

    # RAG Search Type Selection
    rag_search_type_label = tk.Label(content_frame, text="RAG Search Type:", font=("Consolas", 14), bg=BG_COLOR, fg=FG_COLOR)
    rag_search_type_label.grid(row=7, column=0, sticky="w", padx=(0, 10), pady=5)

    rag_search_types = ["similarity", "mmr"]  # Add more types if needed
    rag_search_type_var = tk.StringVar(value=config.get("ragSearchType", "similarity"))
    rag_search_type_combo = ttk.Combobox(content_frame, textvariable=rag_search_type_var, values=rag_search_types, font=("Consolas", 14), height=10)
    rag_search_type_combo.grid(row=7, column=1, sticky="ew", pady=5)

    # RAG Search K Input
    rag_search_k_label = tk.Label(content_frame, text="RAG Search K:", font=("Consolas", 14), bg=BG_COLOR, fg=FG_COLOR)
    rag_search_k_label.grid(row=8, column=0, sticky="w", padx=(0, 10), pady=5)

    rag_search_k_var = tk.StringVar(value=str(config.get("ragSearchK", 5)))
    rag_search_k_entry = ttk.Entry(content_frame, textvariable=rag_search_k_var, font=("Consolas", 14))
    rag_search_k_entry.grid(row=8, column=1, sticky="ew", pady=5)

    # RAG Chunk Size Input (New)
    rag_chunk_size_label = tk.Label(content_frame, text="RAG Chunk Size:", font=("Consolas", 14), bg=BG_COLOR, fg=FG_COLOR)
    rag_chunk_size_label.grid(row=9, column=0, sticky="w", padx=(0, 10), pady=5)

    rag_chunk_size_var = tk.StringVar(value=str(config.get("ragChunkSize", 1000)))
    rag_chunk_size_entry = ttk.Entry(content_frame, textvariable=rag_chunk_size_var, font=("Consolas", 14))
    rag_chunk_size_entry.grid(row=9, column=1, sticky="ew", pady=5)

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
    save_button.grid(row=10, column=0, columnspan=2, pady=20, sticky="we")

    # Configure grid weights
    content_frame.columnconfigure(1, weight=1)

    config_window.bind("<Configure>", on_update_window)

    return config_window