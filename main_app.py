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
        

    def _setup_gui(self):
        self.btn_frame =tk.Frame(self, bd=2, relief = 'groove')
        self.btn_frame.pack(side='left', fill='x')

        load_btn = tk.Button(self.btn_frame, text = "Load files", command = self.create_new_project)
        load_btn.grid(column=0,row=0)

        filter_btn = tk.Button(self.btn_frame, text = 'Filter experiments', command = self.filter_experiments)
        filter_btn.grid(column=1,row=0)

        filtering_tree_frame = tk.Frame(self.btn_frame)
        filtering_tree_frame.grid(column=0,row=1,columnspan=2)
        self.filtered_tree = ttk.Treeview(filtering_tree_frame)        
        self.filtered_tree.pack(side='left', fill ='y')
        vsb = ttk.Scrollbar(filtering_tree_frame, orient="vertical", command=self.filtered_tree.yview)
        vsb.pack(side='right', fill='y')
        self.filtered_tree.configure(yscrollcommand= vsb.set)
        self.filtered_tree.bind("<<TreeviewSelect>>", self.plot_selected)


        #tk.Button(self.btn_frame, text = 'Add "i" to tree', command = self.set_tree_data).pack()
        #tk.Button(self.btn_frame, text = 'Print current tree selection', command = lambda: print(self.filtered_tree.item(self.filtered_tree.selection(),"values"))).pack()
        #export_btn = tk.Button(self.btn_frame, text = 'Process and export data', command = self.process_and_save)
        #export_btn.pack()

        #PREVIEW FRAME
        
        self.preview_figure, self.preview_ax = plt.subplots()
        self.preview_figure.set_size_inches(5,5)
        self.preview_frame = tk.Frame(self, width = 50, height = 50)
        self.preview_ax.set_position((0.15,0.15, 0.75, 0.75))

        self.preview_frame.pack(side='right')
        self.preview_canvas = FigureCanvasTkAgg(self.preview_figure, self.preview_frame)
        self.preview_canvas.get_tk_widget().pack()

        tk.Button(self.preview_frame, text = 'Plot selected', command = self.plot_selected).pack()


    def redirect_function_to_selection(self):
        #A function that redirects the selection from treeview to particular function - e.g. the top level plots all the curves, the next level only one curve,
        # while the column asks for selection between x or y ploting, and then sends that to

        event_id = None
        level =  self.get_tree_level()
        if level == 0:
            self.plot_selected(event_id) 
        elif level == 1:
            self.plot_selected(event_id)
        elif level ==2:
            self.asses_whether_to_classify

    def get_selected(self):
        #Function to get items from the treeview and retrieve experiment data
        pass


    def plot_selected(self, event):
        #Need to change this function!

        self.clear_plot(self.preview_ax)

        selected_items = self.filtered_tree.selection()

        if not selected_items:
            return

        
        #The selection tuple is made up of strings -> need to convert them or check for strings (e.g None in get_data())

        #This ensures different behavior dependent on level
        for selected_item in selected_items:
            level = self.get_tree_level(selected_item)
            if level == 2:
                continue

            selection_tuple = self.filtered_tree.item(selected_item, "values")

            exp = self.manager.filter_by_id(selection_tuple[0]) 
            data = exp.get_data(index = selection_tuple[1], data_type = 'processed_data') #RETURNS A LIST: Experiment.data_list or ...data_list[index], depending on whether or not 
                                                    #whole experiment was selected or just a curve
            x_column, y_column = exp.get_columns()
            name = getattr(exp, 'file_path')

            for curve in data:
                    x = curve[x_column]
                    try:
                        y = curve[selection_tuple[2]]
                    except:
                        y = curve[y_column]

                    self.preview_ax.plot(x,y, label = f'{os.path.basename(name)}')
                    plt.ticklabel_format(axis='y', style = 'sci', scilimits=(-2,3))

                    if isinstance(exp, EIS):
                        self._set_equal_axis_limits(self.preview_ax)


            self.preview_ax.set_xlabel(x_column)
            self.preview_ax.set_ylabel(y_column)
            self.preview_ax.legend()
            self.preview_canvas.draw()

        
    def get_tree_level(self, item_id):
        level = 0
        while self.filtered_tree.parent(item_id):
            item_id = self.filtered_tree.parent(item_id)
            level += 1
        return level

    def clear_plot(self, ax: plt.Axes):
        ax.clear()

    def _set_equal_axis_limits(self, ax: plt.Axes):
        """Adjust plot so X and Y have the same limits and scale."""
        print('elo')
        x_min, x_max = ax.get_xlim()
        y_min, y_max = ax.get_ylim()
        lim_min = min(x_min, y_min)
        lim_max = max(x_max, y_max)
        ax.set_xlim(lim_min, lim_max)
        ax.set_ylim(lim_min, lim_max)
        return

    def set_tree_data(self, experiment_list: list[Experiment]):
        
        self.filtered_tree.delete(*self.filtered_tree.get_children())

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
            self.set_tree_data(experiments)


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
        self.set_tree_data(self.manager.get_experiments('all'))

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



