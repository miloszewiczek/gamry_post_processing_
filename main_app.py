from core import ExperimentLoader, ExperimentManager, VisualizerWindow
import json
from app_config import messages, settings
from experiments import *
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
import os
from tkinter import messagebox
from gui.functions import variable_separation
from functions.functions import calculate_slopes
from tkinter.filedialog import asksaveasfilename
#from gui.tafel_window import tafel_window
import copy
import ttkbootstrap as ttk
from gui import ExperimentTree, FileManagementFrame, PreviewImageFrame, ConfigFrame, TreeController, AnalysisTree
from utilities.utilities import convert_to_zview


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

        self.filtered_tree_frame = ExperimentTree(self, self.manager, self.loader)
        self.filtered_tree_frame.grid(row = 1, column = 0, sticky = 'news', padx = 5, pady = 10)
        self.filtered_tree_controller = self.filtered_tree_frame.get_controller()
        
        #BUTTON FRAME
        self.file_management_frame = FileManagementFrame(self, self.filtered_tree_controller)
        self.file_management_frame.grid(row = 0, column= 0, sticky = 'nsew', padx = 5, pady = 10)

        #CONFIG SECTION FRAME
        self.config_frame = ConfigFrame(self, self.filtered_tree_controller)
        self.config_frame.grid(column = 1, row = 0, sticky = 'nsew', padx = 5, pady = 10)
       
        #PREVIEW IMAGE FRAME
        self.preview_image_frame = PreviewImageFrame(self, self.filtered_tree_controller)
        self.preview_image_frame.grid(row = 1, column = 1, sticky = 'ns')


        #CHRONOP_BTN (TEMPRORARY)
        #tk.Button(self.button_frame, text = 'Process chronop', command = self.process_chronop).grid(row=3, column =0)
        #tk.Button(self.button_frame, text = 'Join', command = self.join).grid(row=3, column = 1)

        self.analysis = AnalysisTree(self, columns = ('analysis',), headers = ('Analysis',), sizes = (100,))
        self.analysis.grid(row = 0, column = 2, sticky = 'nsew', rowspan = 2)


        menubar = tk.Menu(self, tearoff = 0)

        file_menu = tk.Menu(menubar, tearoff = 0)
        file_menu.add_command(label = 'Open', command = lambda: self.filtered_tree_controller.load_from_files('replace'))
        file_menu.add_command(label = 'Open folder', command = lambda: self.filtered_tree_controller.load_from_folder('replace'))
        file_menu.add_separator()
        file_menu.add_command(label = 'Append file', command = lambda: self.filtered_tree_controller.load_from_files('append'))
        file_menu.add_command(label = 'Append folder', command = lambda: self.filtered_tree_controller.load_from_folder('append'))

        experiment_menu = tk.Menu(menubar, tearoff = 0)
        experiment_menu.add_command(label = 'Process', command = self.filtered_tree_controller.process)
        experiment_menu.add_command(label = 'Define experiment', command = lambda: print('Define. WIP!'))
        experiment_menu.add_separator()
        experiment_menu.add_command(label = 'Load settings', command = self.config_frame.load_settings)
        experiment_menu.add_command(label = 'Save settings', command = self.config_frame.dump)
        experiment_menu.add_command(label = 'Apply', command = self.config_frame.apply)

        analysis_menu = tk.Menu(menubar, tearoff = 0)
        analysis_menu.add_command(label = 'Double layer', command = self.cdl_slider)
        analysis_menu.add_command(label = 'Tafel', command = self.tafel_plot)
        analysis_menu.add_command(label = 'Overpotential', command = self.overpot)
        analysis_menu.add_command(label = 'Uncompensated resistance', command = self.Ru_estimation)
        analysis_menu.add_command(label = 'Chronopoints', command = self.chronop)

        utilities_menu = tk.Menu(menubar, tearoff = 0)
        utilities_menu.add_command(label = 'Convert Gamry to ZView', command = convert_to_zview)

        menubar.add_cascade(label = 'File', menu = file_menu)
        menubar.add_cascade(label = 'Experiment', menu = experiment_menu)
        menubar.add_cascade(label = 'Analysis', menu = analysis_menu)
        menubar.add_cascade(label = 'Utilities', menu = utilities_menu)

        self.config(menu = menubar)

    def overpot(self):
        from functions.functions import calc_closest_value
        d = self.filtered_tree_controller.get_experiments('selection')
        currents = variable_separation(self.current.get(), ',', float)
        #divide to obtain A/cm2
        currents = [current/1000 for current in currents]
        columns = ['E_iR vs RHE [V]', 'J_GEO [A/cm2]']
        x = []
        for exp in d:
            df = exp.get_columns(columns = columns)
            pot = df[columns[0]]
            cur = df[columns[1]]
            c = pd.DataFrame([calc_closest_value(currents, cur, pot, mode = 'first')], index = [exp.file_name], columns = currents)
            x.append(c)
        x = pd.concat(x)
        x_transf = x.T
        x_transf['mean'] = x_transf.mean(axis = 1)
        x_transf['std'] = x_transf.std(axis = 1)
        self.analysis.add_analysis(x_transf, aux = {'Dopa': 'dopa'})

    def Ru_estimation(self):
        from gui.Ru_estimator import RuEstimate
        d = self.manager.filter(object_type = [LinearVoltammetry, Voltammetry, ECSA])
        window = RuEstimate(self, self.manager, self.loader, lambda x: self.config_frame.Ru_var.set(x), nodes = d)


    def tafel_plot(self):
        from gui.tafel_window import tafel_window
        d = self.manager.filter(object_type = LinearVoltammetry)
        window = tafel_window(self, d, callback = self.receive)
    
    def cdl_slider(self):
        from gui.slider import InteractivePlotApp
        d = self.manager.filter(object_type = Voltammetry)
        window = InteractivePlotApp(self, d, callback = self.receive)

    def chronop(self):
        from gui.chronopoints import ChronoPicker
        d = self.manager.filter(object_type = Chronoamperometry)
        data = d[0].get_columns(['T [s]', 'J_GEO [A/cm2]'])
        x, y = data
        window = ChronoPicker(self, nodes = None, callback = None, x = data['T [s]'], y = data['J_GEO [A/cm2]'])

        
    
    def receive(self, values, aux, name,):
        self.analysis.add_analysis(values, aux, name, False)



if __name__ == '__main__':
    app = ExperimentOrchestrator()
    app.mainloop()



