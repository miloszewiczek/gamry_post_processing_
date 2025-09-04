import tkinter as tk
from tkinter import ttk
from .functions import load_files, append_files, process_and_save, process, load_folder

class FileManagementFrame(ttk.Labelframe):
    def __init__(self, parent):
        super().__init__(parent, text = 'File Management')
        self.loader = parent.loader
        self.manager = parent.manager

        self.load_files_btn = tk.Button(self, text = 'Load', command = lambda: load_files(self.loader, parent.filtered_tree, self.manager))
        self.load_files_btn.grid(row = 0, column = 0, padx = 10)

        self.load_folder_btn = tk.Button(self, text = 'Choose folder', command = lambda: load_folder(self.loader, parent.filtered_tree, self.manager))
        self.load_folder_btn.grid(row = 1, column = 0, padx = 10)

        tk.Button(self, text = 'Append', command = lambda: append_files(self.loader, parent.filtered_tree, self.manager)).grid(row=0,column=1)
        tk.Button(self, text = 'Save all', command = lambda: process_and_save(parent.filtered_tree, self.manager)).grid(row=0,column=2)

        tk.Button(self, text = 'Node test', comman= lambda: process(parent.filtered_tree, self.manager, selection_mode = 'selected')).grid(row=0,column=3)
        tk.Button(self, text = 'Node test all', comman= lambda: process(parent.filtered_tree, self.manager, selection_mode= 'all')).grid(row=1,column=3)