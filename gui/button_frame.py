import tkinter as tk
from tkinter import ttk
from .functions import process_and_save, process, load
from .tree_controller import TreeController

class FileManagementFrame(ttk.Labelframe):
    def __init__(self, parent, controller: TreeController):
        super().__init__(parent, text = 'File Management')
        self.loader = parent.loader
        self.manager = parent.manager
        self.controller = controller

        self.load_files_btn = tk.Button(self, text = 'Load Files', command = lambda: self.controller.load_from_files('replace'))
        self.append_files_btn = tk.Button(self, text = 'Append Files', command = lambda: self.controller.load_from_files('append'))
        self.load_folder_btn = tk.Button(self, text = 'Load Folder', command = lambda: self.controller.load_from_folder('replace'))
        self.append_folder_btn = tk.Button(self, text = 'Append Folder', command = lambda: self.controller.load_from_folder('append'))

        self.buttons = [self.load_files_btn, self.append_files_btn, self.load_folder_btn, self.append_folder_btn]
        
        for button in self.buttons:
            button.pack(side = 'left', padx = 2, pady = 2, ipadx = 2, ipady = 2)
        