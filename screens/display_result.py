import multiprocessing
from queue import Empty
import threading
from ai.rag_functions import query_rag
from globals import MAIN_WINDOW, BG_COLOR, BTN_BG_COLOR, FG_COLOR
import tkinter as tk
import markdown2
from tkinter import scrolledtext
import pyperclip
from tkinterweb import HtmlFrame

def display_result(transcript, result, content_type="markdown"):
    response_queue = multiprocessing.Queue()
    result_window = tk.Toplevel(MAIN_WINDOW)
    result_window.title("Result")
    result_window.configure(bg=BG_COLOR)
    result_window.geometry("1200x768")
    result_window.configure(padx=20, pady=20)

    def copy_to_clipboard(content):
        pyperclip.copy(content)

    # Create main frame
    main_frame = tk.Frame(result_window, bg=BG_COLOR)
    main_frame.grid(row=0, column=0, sticky="nsew")

    # Create sidebar frame
    sidebar_frame = tk.Frame(result_window, bg=BG_COLOR)
    sidebar_frame.grid(row=0, column=1, sticky="nsew", padx=(20, 0))
    # sidebar_frame.grid_propagate(
    #     False
    # )  # Prevent the frame from resizing based on its content

    # Configure the grid to allocate space to the frames
    result_window.grid_columnconfigure(0, weight=1)
    result_window.grid_columnconfigure(1, weight=3)
    result_window.grid_rowconfigure(0, weight=1)

    # Button frame in main content
    button_frame = tk.Frame(main_frame, bg=BG_COLOR)
    button_frame.pack(pady=(0, 10), anchor=tk.W)

    copy_transcript = tk.Button(
        button_frame,
        text="Copiar transcript",
        command=lambda: copy_to_clipboard(transcript),
        bg=BTN_BG_COLOR,
        fg=FG_COLOR,
        font=("Consolas", 14),
    )
    copy_transcript.pack(side=tk.LEFT, padx=(0, 5))

    copy_markdown = tk.Button(
        button_frame,
        text="Copiar Markdown",
        command=lambda: copy_to_clipboard(result),
        bg=BTN_BG_COLOR,
        fg=FG_COLOR,
        font=("Consolas", 14),
    )
    copy_markdown.pack(side=tk.LEFT, padx=5)

    copy_html = tk.Button(
        button_frame,
        text="Copiar HTML",
        command=lambda: copy_to_clipboard(styled_html_content),
        bg=BTN_BG_COLOR,
        fg=FG_COLOR,
        font=("Consolas", 14),
    )
    copy_html.pack(side=tk.LEFT, padx=(5, 0))

    if content_type == "markdown":
        html_content = markdown2.markdown(result, extras=["break-on-newline"])
        styled_html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
            <style>
            html {{
                margin: 0;
                padding: 0;
                height: 100%;
                background-color: {BG_COLOR};
                color: #CCC;
                font-family: 'Consolas', monospace;
                font-size: 18px;
            }}
            body {{
                padding: 0 20px 50px 0;
            }}
            </style>
            </head>
            <body>
            <div>{html_content}</div>
            </body>
            </html>
            """
        # messages_enabled es para evitar unos mensajes como de debiug que muestra por defecto
        html_frame = HtmlFrame(main_frame, messages_enabled=False)
        html_frame.load_html(styled_html_content)
        html_frame.pack(expand=True, fill=tk.BOTH)
    else:
        text_area = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            font=("Helvetica", 16),
            bg=BG_COLOR,
            fg="#CCC",
            insertbackground=BG_COLOR,
        )
        text_area.pack(expand=True, fill=tk.BOTH)
        text_area.insert(tk.END, result)
        text_area.config(state=tk.DISABLED)

    # Sidebar content
    sidebar_label = tk.Label(
        sidebar_frame,
        text="Chat",
        bg=BG_COLOR,
        fg=FG_COLOR,
        font=("Consolas", 16, "bold"),
    )
    sidebar_label.pack(pady=(0, 10))

    conversation_area = scrolledtext.ScrolledText(
        sidebar_frame,
        wrap=tk.WORD,
        font=("Consolas", 14),
        bg=BG_COLOR,
        fg="#CCC",
        insertbackground="#CCC",
    )
    conversation_area.pack(fill=tk.BOTH, expand=True,pady=(0, 30), ipadx=10, ipady=10)

    input_area = tk.Text(
        sidebar_frame,
        wrap=tk.WORD,
        font=("Consolas", 14),
        bg=BG_COLOR,
        fg="#CCC",
        insertbackground="#CCC",
        height=2
    )
    input_area.pack(fill=tk.X, pady=(0, 10))

    def send_message():
        user_message = input_area.get("1.0", tk.END).strip()
        if user_message:
            conversation_area.config(state=tk.NORMAL)
            conversation_area.insert(tk.END, f"Tu: {user_message}\n\n")
            conversation_area.config(state=tk.DISABLED)
            conversation_area.see(tk.END)
            input_area.delete("1.0", tk.END)

            # Disable the send button and input area while processing
            send_button.config(state=tk.DISABLED)
            input_area.config(state=tk.DISABLED)

            # Display a "thinking" message
            conversation_area.config(state=tk.NORMAL)
            conversation_area.insert(tk.END, "NIA: Pensando...\n\n")
            conversation_area.config(state=tk.DISABLED)
            conversation_area.see(tk.END)

            # Function to run query_rag in a separate thread
            def rag_thread():
                try:
                    rag_response = query_rag(user_message, True)
                    response_queue.put(("success", rag_response))
                except Exception as e:
                    response_queue.put(("error", str(e)))

            # Start the RAG query in a separate thread
            threading.Thread(target=rag_thread, daemon=True).start()

            # Function to check for RAG response
            def check_response():
                try:
                    response_type, response = response_queue.get_nowait()
                    conversation_area.config(state=tk.NORMAL)
                    # Remove the "thinking" message
                    conversation_area.delete("end-3l", "end-1l")
                    if response_type == "success":
                        conversation_area.insert(tk.END, f"NIA: {response}\n\n")
                    else:
                        conversation_area.insert(tk.END, f"Error: {response}\n\n")
                    conversation_area.config(state=tk.DISABLED)
                    conversation_area.see(tk.END)
                    # Re-enable the send button and input area
                    send_button.config(state=tk.NORMAL)
                    input_area.config(state=tk.NORMAL)
                except Empty:
                    # If no response yet, check again after 100ms
                    result_window.after(100, check_response)

            # Start checking for the response
            result_window.after(100, check_response)

    send_button = tk.Button(
        sidebar_frame,
        text="Enviar",
        command=send_message,
        bg=BTN_BG_COLOR,
        fg=FG_COLOR,
        font=("Consolas", 16),
        height=1,
        bd=0
    )
    send_button.pack(fill=tk.X)

    # Bind Enter key to send_message function
    input_area.bind("<Return>", lambda event: send_message())

    return result_window
