from core import ExperimentLoader, ExperimentManager, VisualizerWindow
import json
from app_config import messages, settings
from experiments import *
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt

import os
from tkinter import messagebox
from utilities.other import *
from functions.functions import calculate_slopes
from tkinter.filedialog import asksaveasfilename
from gui.tafel_window import tafel_window
import copy
import ttkbootstrap as ttk
from gui import ExperimentTree, FileManagementFrame, PreviewImageFrame, ConfigFrame


class ExperimentOrchestrator(ttk.Window):
    def __init__(self):
        super().__init__(themename = 'flatly')
        self.title('Miloszs app for electrochemical data!')
        self.loader = ExperimentLoader()
        self.manager = ExperimentManager()
        self.tmp = []
        
        self._setup_gui()
        #self.bind('<Escape>', lambda event: self.destroy())

    def _setup_gui(self):
  
        #FILTERING TREE
        #CONFIGURE FILTERING TREE SIZE
        self.columnconfigure(0, minsize = 350, weight = 0)
        self.rowconfigure(0, weight = 0, minsize = 50)
        self.rowconfigure(1, weight = 1)
        self.columnconfigure(1, weight = 1)

        self.filtered_tree_frame = ExperimentTree(self)
        self.filtered_tree_frame.grid(row = 1, column = 0, sticky = 'news', padx = 5, pady = 10)
        self.filtered_tree = self.filtered_tree_frame.tree
        
        #BUTTON FRAME
        self.file_management_frame = FileManagementFrame(self)
        self.file_management_frame.grid(row = 0, column= 0, sticky = 'nsew', padx = 5, pady = 10)

        #CONFIG SECTION FRAME
        self.config_frame = ConfigFrame(self)
        self.config_frame.grid(column = 1, row = 0, sticky = 'nsew', padx = 5, pady = 10)
       
        #PREVIEW IMAGE FRAME
        self.preview_image_frame = PreviewImageFrame(self)
        self.preview_image_frame.grid(row = 1, column = 1, sticky = 'nsew')


        self.cdl_slider_button = tk.Button(self, text='CDL Slider', command = self.cdl_slider)
        self.cdl_slider_button.grid(column = 2, row = 2)

        #TAFEL BTN
        #tk.Button(self.button_frame, text = 'Calculate Tafel', command = self.tafel_plot).grid(row=2, column=0)

        #CHRONOP_BTN (TEMPRORARY)
        #tk.Button(self.button_frame, text = 'Process chronop', command = self.process_chronop).grid(row=3, column =0)
        #tk.Button(self.button_frame, text = 'Join', command = self.join).grid(row=3, column = 1)



    def tafel_plot(self):
        experiment = self.manager.filter(object_type=LinearVoltammetry)
        tafel_w = tafel_window(self)
        set_tree_data(tafel_w.data_treeview, experiment)
        
    
    def cdl_slider(self):
        from gui.slider import InteractivePlotApp
        d = self.manager.filter(object_type = Voltammetry)
        window = InteractivePlotApp(self)
        set_tree_data(window.data_treeview, d)


if __name__ == '__main__':
    app = ExperimentOrchestrator()
    app.mainloop()



