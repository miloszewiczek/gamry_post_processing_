from core import ExperimentLoader, ExperimentManager, VisualizerWindow
import json
from app_config import messages, settings
from experiments import *
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class ExperimentOrchestrator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Miloszs app for electrochemical data!')
        self.geometry('1200x800')

        self.loader = ExperimentLoader()
        self.manager = ExperimentManager()
        
        self._setup_gui()


    def _setup_gui(self):
        btn_frame =tk.Frame(self)
        btn_frame.pack(fill='x')

        load_btn = tk.Button(btn_frame, text = "Load files", command = self.create_new_project)
        load_btn.pack()

        export_btn = tk.Button(btn_frame, text = 'Process and export data', command = self.process_and_save)
        export_btn.pack()

        filter_btn = tk.Button(btn_frame, text = 'Filter experiments', command = self.filter_experiments)
        filter_btn.pack()

    def filter_experiments(self):

        top = tk.Toplevel(self)
        top.title('Filtering')
        tk.Label(top, text = 'Please input the filtering keys.').pack()

        tk.Label(top, text = 'Name filter:').pack()
        name_filter = tk.Entry(top)
        name_filter.pack()

        tk.Label(top, text = 'Cycle filter:').pack()
        cycle_filter = tk.Entry(top)
        cycle_filter.pack()

        tk.Label(top, text = 'Object filter:').pack() #ADD A DROPDOWN
        
        object_filter = ttk.Combobox(top, values = self.manager.get_unique_experiments()) 
        object_filter.pack()
        object_filter.set('<choose an object>')

        #ADD BIND METHOD OVERALL! (WANTED TO MAKE A HOVER OVER EXPLANATION)



    def process_and_save(self, save_name = None):

        if save_name is None:
            top = tk.Toplevel(self)
            top.title('No save name!')
            tk.Label(top, text = 'No save name. Please insert it below').pack()
            save_name_entry = tk.Entry(top)
            save_name_entry.pack()
            tk.Button(top, text = 'OK', command = lambda: self.get_entry_and_destroy(entry = save_name_entry,
                                                                                     popup = top)
                                                                                     ).pack() 

        #self.manager.batch_process_selected_experiments(save_name)

    def create_new_project(self):
        list_of_experiments = self.loader.choose_folder()
        self.manager.set_experiments(list_of_experiments)
        print(self.manager.list_of_experiments)

    def get_entry_and_destroy(self, entry:tk.Entry, popup: tk.Toplevel):
        self.tmp = entry.get()
        print(self.tmp)
        popup.destroy()
        return
    
if __name__ == '__main__':
    app = ExperimentOrchestrator()
    app.mainloop()



