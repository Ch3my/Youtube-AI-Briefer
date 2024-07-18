import tkinter as tk

# SINGLETON PATTERN
class Globals:
    def __init__(self):
        self.MAIN_WINDOW = tk.Tk()
        self.BG_COLOR = "#2E2E2E"
        self.FG_COLOR = "#FFFFFF"
        self.BTN_BG_COLOR = "gray"
        self.ENTRY_BG_COLOR = "#3C3C3C"
        self.ENTRY_FG_COLOR = "#FFFFFF"
        self.FEEDBACK_MSG = ""
        self.CONFIG_FILE = "config.json"
        self.AVAILABLE_MODELS = ["claude-3-haiku-20240307", "claude-3-5-sonnet-20240620", "gpt-4o-mini", "gpt-4o"]

    def get_feedback_msg(self):
        return self.FEEDBACK_MSG

    def set_feedback_msg(self, msg):
        self.FEEDBACK_MSG = msg
        # Update the label text
        if hasattr(self, 'feedback_label'):
            self.feedback_label.config(text=msg)

# Create a single instance of Globals
globals_instance = Globals()

# Define module-level variables
MAIN_WINDOW = globals_instance.MAIN_WINDOW
BG_COLOR = globals_instance.BG_COLOR
FG_COLOR = globals_instance.FG_COLOR
BTN_BG_COLOR = globals_instance.BTN_BG_COLOR
ENTRY_BG_COLOR = globals_instance.ENTRY_BG_COLOR
ENTRY_FG_COLOR = globals_instance.ENTRY_FG_COLOR
FEEDBACK_MSG = globals_instance.FEEDBACK_MSG
CONFIG_FILE = globals_instance.CONFIG_FILE
AVAILABLE_MODELS = globals_instance.AVAILABLE_MODELS

# Define a function to get feedback message
def get_feedback_msg():
    return globals_instance.get_feedback_msg()

# Define a function to set feedback message
def set_feedback_msg(msg):
    globals_instance.set_feedback_msg(msg)