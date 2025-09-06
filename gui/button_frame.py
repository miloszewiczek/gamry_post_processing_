import tkinter as tk
from tkinter import ttk
from .functions import append, process_and_save, process, load, append

class FileManagementFrame(ttk.Labelframe):
    def __init__(self, parent):
        super().__init__(parent, text = 'File Management')
        self.loader = parent.loader
        self.manager = parent.manager
        self.tree = parent.filtered_tree

        self.load_files_btn = tk.Button(self, text = 'Load Files', command = lambda: load(self.loader, parent.filtered_tree, self.manager, from_ = 'files'))

        self.load_folder_btn = tk.Button(self, text = 'Load Folder', command = lambda: load(self.loader, parent.filtered_tree, self.manager, from_ = 'folder'))
   
        self.append_files_btn = tk.Button(self, text = 'Append Files', command = lambda: append(self.loader, parent.filtered_tree, self.manager, from_ = 'files'))

        self.append_folder_btn = tk.Button(self, text = 'Append Folder', command = lambda: append(self.loader, parent.filtered_tree, self.manager, from_ = 'folder'))
        
        self.save_btn = tk.Button(self, text = 'Save', command = lambda: process_and_save(self.tree, self.manager))
        
        
        self.buttons = [self.load_files_btn, self.load_folder_btn, self.append_files_btn, self.append_folder_btn, self.save_btn]
        
        for button in self.buttons:
            button.pack(side = 'left', padx = 2, pady = 2, ipadx = 2, ipady = 2)
        

                 #PROCESSING BUTTONS