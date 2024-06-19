from globals import MAIN_WINDOW, BG_COLOR, BTN_BG_COLOR, FG_COLOR
import tkinter as tk
import markdown2
from tkinter import scrolledtext
from tkhtmlview import HTMLLabel
import pyperclip

# Function to display the result in a new window
def display_result(result, content_type="markdown"):
    padding = 20
    result_window = tk.Toplevel(MAIN_WINDOW)
    result_window.title("Result")
    result_window.configure(bg=BG_COLOR)
    result_window.geometry("800x768")
    # Add padding around the entire window
    result_window.configure(padx=padding, pady=padding)

    # Function to copy text to clipboard
    def copy_to_clipboard():
        pyperclip.copy(result)  # Copy content to clipboard

    copy_button = tk.Button(
        result_window,
        text="Copiar contenido",
        command=copy_to_clipboard,
        bg=BTN_BG_COLOR,
        fg=FG_COLOR,
        font=("Consolas", 16),
    )
    copy_button.pack(pady=(0, 10), anchor="w")

    if content_type == "markdown":
        # Convert Markdown to HTML
        html_content = markdown2.markdown(result)
        styled_html_content = f'<div style="color: #CCC;">{html_content}</div>'

        # Use tkhtmlview to display HTML content
        html_label = HTMLLabel(
            result_window,
            html=styled_html_content,
            background=BG_COLOR,
            foreground="#FFFFFF",
        )
        html_label.pack(expand=True, fill=tk.BOTH)
    else:
        # Plain text display
        text_area = scrolledtext.ScrolledText(
            result_window,
            wrap=tk.WORD,
            font=("Helvetica", 12),
            bg="white",
            fg="black",
            insertbackground="black",
        )
        text_area.pack(expand=True, fill=tk.BOTH)
        text_area.insert(tk.END, result)
        text_area.config(state=tk.DISABLED)
