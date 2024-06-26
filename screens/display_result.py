from globals import MAIN_WINDOW, BG_COLOR, BTN_BG_COLOR, FG_COLOR
import tkinter as tk
import markdown2
from tkinter import scrolledtext
import pyperclip
from tkinterweb import HtmlFrame

# Function to display the result in a new window
def display_result(transcript, result, content_type="markdown"):
    result_window = tk.Toplevel(MAIN_WINDOW)
    result_window.title("Result")
    result_window.configure(bg=BG_COLOR)
    result_window.geometry("800x768")
    # Add padding around the entire window
    result_window.configure(padx=20, pady=20)

    # Function to copy text to clipboard
    def copy_to_clipboard(content):
        pyperclip.copy(content)  

    # Create a frame to hold the buttons
    button_frame = tk.Frame(result_window, bg=BG_COLOR)
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
        # Convert Markdown to HTML
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
        html_frame = HtmlFrame(result_window, messages_enabled=False)
        html_frame.load_html(styled_html_content)
        html_frame.pack(expand=True, fill=tk.BOTH)
    else:
        # Plain text display
        text_area = scrolledtext.ScrolledText(
            result_window,
            wrap=tk.WORD,
            font=("Helvetica", 16),
            bg=BG_COLOR,
            fg="#CCC",
            insertbackground=BG_COLOR,
        )
        text_area.pack(expand=True, fill=tk.BOTH)
        text_area.insert(tk.END, result)
        text_area.config(state=tk.DISABLED)
