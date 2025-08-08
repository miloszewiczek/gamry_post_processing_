from core import ExperimentLoader, ExperimentManager, VisualizerWindow
import json
from app_config import messages, settings
from experiments import *
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os

class ExperimentOrchestrator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Miloszs app for electrochemical data!')
        self.geometry('1200x800')

        self.loader = ExperimentLoader()
        self.manager = ExperimentManager()
        
        self._setup_gui()
        self.filtered_tree = ttk.Treeview(self)
        self.filtered_tree.pack()

    def _setup_gui(self):
        self.btn_frame =tk.Frame(self)
        self.btn_frame.pack(fill='x')

        load_btn = tk.Button(self.btn_frame, text = "Load files", command = self.create_new_project)
        load_btn.pack()

        export_btn = tk.Button(self.btn_frame, text = 'Process and export data', command = self.process_and_save)
        export_btn.pack()

        filter_btn = tk.Button(self.btn_frame, text = 'Filter experiments', command = self.filter_experiments)
        filter_btn.pack()

        tk.Button(self.btn_frame, text = 'Add "i" to tree', command = self.add_to_tree_data).pack()
        tk.Button(self.btn_frame, text = 'Print current tree selection', command = lambda: print(self.filtered_tree.item(self.filtered_tree.selection(),"values"))).pack()



        #PREVIEW FRAME
        self.figure, self.ax = plt.subplots()
        self.preview_frame = tk.Frame(self)
        self.preview_frame.pack(fill='x')
        self.preview_canvas = FigureCanvasTkAgg(self.figure, self.preview_frame)
        self.preview_canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Button(self.preview_frame, text = 'Plot selected', command = self.plot_selected).pack()

    def plot_selected(self):
        #THE FUNCTIONALITY IS KIND OF LIMITED TO 1 SELECTION NOW. WHEN MULTISELECTION IS USED, THE SELECTION SPANS FORM THE PARENT TO THE CHILDREN, MAKING THE FUNCTION UNUSABLE
        selected_items = self.filtered_tree.selection()
        if not selected_items:
            return
        print(selected_items)
        
        #The selection tuple is made up of strings -> need to convert them or check for strings (e.g None in get_curves())
        selection_tuple = self.filtered_tree.item(selected_items, "values")
        print(selection_tuple)
        exp = self.manager.filter_by_id(selection_tuple[0]) 
        data = exp.get_curves(index = selection_tuple[1]) #RETURNS A LIST: Experiment.data_list or ...data_list[index], depending on whether or not 
                                                #whole experiment was selected or just a curve
        for curve in data:
            x, y = curve['Vf'], curve['Im']
            self.ax.plot(x,y)

            

        self.preview_canvas.draw()

        
        

    def add_to_tree_data(self, experiment_list: list[Experiment]):

        for exp in experiment_list:
            path = os.path.basename(exp.file_path)
            path_node = self.filtered_tree.insert('', index='end', text = path, open = False, values = (exp.id, None))
            
            if not hasattr(exp, 'data_list'):
                exp.load_data()
                exp.process_data()

            for i, curve in enumerate(exp.processed_data):
                curve_node = self.filtered_tree.insert(path_node, 'end', text = f'Curve {i}', open = False, values = (exp.id, i))
                
                for column in curve.columns:
                    column_node = self.filtered_tree.insert(curve_node, 'end', text = column, values = (exp.id, i, column))

    def filter_experiments(self):

        def filter():
            name_filter, cycle_filter, object_type_filter = self.get_entry_and_destroy(entries= [name_filter_entry, 
                                                                                                cycle_filter_entry,
                                                                                                object_filter_combobx,],
                                                                                    store_atr = 'filtered',
                                                                                    popup = top)
            
            experiments = self.manager.filter(name = name_filter, 
                                              cycle = cycle_filter, 
                                              object_type= object_type_filter,
                                              inclusive = var.get())
            
            self.filtered_tree.delete(*self.filtered_tree.get_children())
            self.add_to_tree_data(experiments)


        top = tk.Toplevel(self)
        top.title('Filtering')
        tk.Label(top, text = 'Please input the filtering keys.').pack()

        tk.Label(top, text = 'Name filter:').pack()
        name_filter_entry = tk.Entry(top)
        name_filter_entry.pack()

        tk.Label(top, text = 'Cycle filter:').pack()
        cycle_filter_entry = tk.Entry(top)
        cycle_filter_entry.pack()

        tk.Label(top, text = 'Object filter:').pack() #ADD A DROPDOWN
        
        object_filter_combobx = ttk.Combobox(top, values = self.manager.get_unique_experiments()) 
        object_filter_combobx.pack()
        object_filter_combobx.set('<choose an object>')

        #ADD BIND METHOD OVERALL! (WANTED TO MAKE A HOVER OVER EXPLANATION)
        tk.Button(top, text = 'OK', command = filter).pack()
        var = tk.IntVar()
        inclusive_filtering_chckbtn = tk.Checkbutton(top, text = 'Inclusive filtering', variable= var, onvalue = 1, offvalue = 0, )
        inclusive_filtering_chckbtn.pack()
        inclusive_filtering_chckbtn.select()


    def process_and_save(self, save_name = None):

        if save_name is None:
            top = tk.Toplevel(self)
            top.title('No save name!')
            tk.Label(top, text = 'No save name. Please insert it below').pack()
            save_name_entry = tk.Entry(top)
            save_name_entry.pack()
            tk.Button(top, text = 'OK', command = lambda: self.get_entry_and_destroy(entries = save_name_entry,
                                                                                     store_atr = 'save_name',
                                                                                     popup = top)
                                                                                     ).pack() 

        self.manager.batch_process_selected_experiments(save_name)

    def create_new_project(self):
        list_of_experiments = self.loader.choose_folder()
        self.manager.set_experiments(list_of_experiments)
        self.add_to_tree_data(self.manager.get_experiments('all'))

    def get_entry_and_destroy(self, entries:tk.Entry | list[tk.Entry], store_atr, popup: tk.Toplevel):

        if isinstance(entries, list):
            self.tmp = [entry.get() for entry in entries]
        else:
            self.tmp = entries.get()
        
        tmp_None = []

        for entry_data in self.tmp:
            if entry_data in ['', '<choose an object>']:
                tmp_None.append(None)
            else: 
                tmp_None.append(entry_data)

        self.__setattr__(store_atr, tmp_None)

        popup.destroy()
        return tmp_None
    
if __name__ == '__main__':
    app = ExperimentOrchestrator()
    app.mainloop()



