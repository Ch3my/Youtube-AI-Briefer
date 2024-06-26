# Implementation of Collapsible Pane container

# importing tkinter and ttk modules
import tkinter as tk
from tkinter import ttk

# Add the directory containing globals.py to sys.path
# para poder hacer import de algo que esta un directorio mas arriba
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from globals import BTN_BG_COLOR, FG_COLOR, BG_COLOR


class Collapsible(ttk.Frame):
    """
    -----USAGE-----
    collapsiblePane = CollapsiblePane(parent,
                                            expanded_text =[string],
                                            collapsed_text =[string])

    collapsiblePane.pack()
    button = Button(collapsiblePane.frame).pack()
    """

    def __init__(self, parent, expanded_text="Collapse <<", collapsed_text="Expand >>"):

        ttk.Frame.__init__(self, parent)

        # These are the class variable
        # see a underscore in expanded_text and _collapsed_text
        # this means these are private to class
        self.parent = parent
        self._expanded_text = expanded_text
        self._collapsed_text = collapsed_text

        frame_style = ttk.Style()
        frame_style.configure("Custom.TFrame", background=BG_COLOR)  

        # Apply style to the frame
        self.config(style="Custom.TFrame")

        # Here weight implies that it can grow it's
        # size if extra space is available
        # default weight is 0
        self.columnconfigure(1, weight=1)

        # Tkinter variable storing integer value
        self._variable = tk.IntVar()

        # TOGGLE BUTTON
        style = ttk.Style()
        style.configure(
            "Custom.TCheckbutton", background=BTN_BG_COLOR, foreground=FG_COLOR,padding=10
        )
        style.map(
            "Custom.TCheckbutton",
            background=[('!disabled', BTN_BG_COLOR), ('active', BTN_BG_COLOR)],
            foreground=[('!disabled', FG_COLOR), ('active', FG_COLOR)]
        )
        # Hide Checkmark
        style.layout("Custom.TCheckbutton",
            [('Checkbutton.padding', {'children': [('Checkbutton.label', {'side': 'left', 'expand': 1})]})])

        # Checkbutton is created but will behave as Button
        # cause in style, Button is passed
        # main reason to do this is Button do not support
        # variable option but checkbutton do
        self._button = ttk.Checkbutton(
            self,
            variable=self._variable,
            command=self._activate,
            style="Custom.TCheckbutton",
        )
        self._button.grid(row=0, column=0, sticky="ew")

        # This will create a separator
        # A separator is a line, we can also set thickness
        # self._separator = ttk.Separator(self, orient ="horizontal")
        # self._separator.grid(row = 0, column = 1, sticky ="we")

        self.frame = ttk.Frame(self)

        # This will call activate function of class
        self._activate()

    def _activate(self):
        if not self._variable.get():

            # As soon as button is pressed it removes this widget
            # but is not destroyed means can be displayed again
            self.frame.grid_forget()

            # This will change the text of the checkbutton
            self._button.configure(text=self._collapsed_text)

        elif self._variable.get():
            # increasing the frame area so new widgets
            # could reside in this container
            self.frame.grid(row=1, column=0, columnspan=2)
            self._button.configure(text=self._expanded_text)

    def toggle(self):
        """Switches the label frame to the opposite state."""
        self._variable.set(not self._variable.get())
        self._activate()
