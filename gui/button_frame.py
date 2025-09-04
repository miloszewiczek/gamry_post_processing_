import tkinter as tk
from tkinter import ttk
from .functions import create_new_project, append_files, process_and_save

class FileManagementFrame(ttk.Labelframe):
    def __init__(self, parent):
        super().__init__(parent, text = 'File Management')
        self.loader = parent.loader
        self.manager = parent.manager

        self.load_btn = tk.Button(self, text = 'Load', command = lambda: create_new_project(self.loader, parent.filtered_tree, self.manager))
        self.load_btn.grid(row = 0, column = 0, padx = 10)
        tk.Button(self, text = 'Append', command = lambda: append_files(self.loader, parent.filtered_tree, self.manager)).grid(row=0,column=1)
        tk.Button(self, text = 'Save all', command = lambda: process_and_save(parent.filtered_tree, self.manager)).grid(row=0,column=2)