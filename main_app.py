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
from tafel_window import tafel_window
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
  
        #CONFIGURE FILTERING TREE SIZE
        self.columnconfigure(0, minsize=300, weight = 1)
        self.rowconfigure(0, weight=1, minsize = 50)


        #FILTERING TREE
        
        self.filtered_tree_frame = ExperimentTree(self)
        self.filtered_tree_frame.grid(row=1, column = 0)
        self.filtered_tree = self.filtered_tree_frame.filtered_tree
        
        #BUTTON FRAME
        self.file_management_frame = FileManagementFrame(self)
        self.file_management_frame.grid(row = 0, column= 0 )
       
        #PREVIEW IMAGE FRAME
        self.preview_image_frame = PreviewImageFrame(self)
        self.preview_image_frame.grid(row = 1, column = 2)


        #CONFIG SECTION FRAME
        self.config_frame = ConfigFrame(self)
        self.config_frame.grid(column=1, row =0, sticky = 'nsew', pady = 10)


        #CDL SLIDER GUI

        #self.cdl_slider_button = tk.Button(self.preview_frame, text='CDL Slider', command = self.cdl_slider)
        #self.cdl_slider_button.pack()

        #TAFEL BTN
        #tk.Button(self.button_frame, text = 'Calculate Tafel', command = self.tafel_plot).grid(row=2, column=0)

        #CHRONOP_BTN (TEMPRORARY)
        #tk.Button(self.button_frame, text = 'Process chronop', command = self.process_chronop).grid(row=3, column =0)
        #tk.Button(self.button_frame, text = 'Join', command = self.join).grid(row=3, column = 1)


    def print_experiment_data(self):
        experiment = self.filtered_tree.selection()[0]
        exps = map_ids_to_experiments(experiment, self.manager)
        exp = exps[0]['experiment'].data_listex
        print(len(exp))

    def tafel_plot(self):
        experiment = self.manager.filter(object_type=LinearVoltammetry)
        tafel_w = tafel_window(self)
        set_tree_data(tafel_w.data_treeview, experiment)
        
    
    def cdl_slider(self):
        from slider import InteractivePlotApp
        d = self.manager.filter(object_type = Voltammetry)
        window = InteractivePlotApp(self)
        set_tree_data(window.data_treeview, d)


    def filter_experiments(self):

        #ZMIENIĆ FUNCKE FILTER, PO UWZGLĘDNIENIU NOWEJ WERSJI get_entry_and_destroy

        def on_ok():
            #collect values
            name_filter, cycle_filter, object_type_filter = self.get_entry_values(entries= [name_filter_entry, 
                                                                                            cycle_filter_entry,
                                                                                            object_filter_combobx])
        
            #run filtering
            experiments = self.manager.filter(name = name_filter, 
                                            cycle = cycle_filter, 
                                            object_type= object_type_filter,
                                            inclusive = var.get())
        
            #update tree
            set_tree_data(tree_item = self.filtered_tree, experiment_list = experiments, replace = True)

            #close popup
            top.destroy()

            #build a human-readable filtering description
            desc_parts = []
            if name_filter:
                desc_parts.append(f'Name = {name_filter}')
            if cycle_filter:
                desc_parts.append(f'Cycle = {cycle_filter}')
            if object_type_filter:
                desc_parts.append(f'Type = {object_type_filter}')
            desc = " | ".join(desc_parts) if desc_parts else 'No filter applied'

            self.current_filter_var.set(f'Active filter: {desc}')



        def on_cancel():

            top.destroy()
            return

            

        #create a new window with filter entries
        top = tk.Toplevel(self)
        top.title('Filtering')
        tk.Label(top, text = 'Please input the filtering keys.').grid(row=0, column=0, columnspan=2, pady=10, sticky = 'w')

        tk.Label(top, text = 'Name filter:').grid(row=1, column =0, sticky = 'w', padx=10)
        name_filter_entry = tk.Entry(top)
        name_filter_entry.grid(row=1, column = 1, sticky = 'we')

        tk.Label(top, text = 'Cycle filter:').grid(row=2, column = 0, sticky = 'w', padx=10)
        cycle_filter_entry = tk.Entry(top)
        cycle_filter_entry.grid(row=2, column= 1, sticky = 'we')

        tk.Label(top, text = 'Object filter:').grid(row=3, column =0, sticky = 'w', padx=10) 

        #object dropdown    
        object_filter_combobx = ttk.Combobox(top, values = self.manager.get_unique_experiments()) 
        object_filter_combobx.grid(row=3, column = 1, sticky = 'we')
        object_filter_combobx.set('<choose an object>')

        #ADD BIND METHOD OVERALL! (WANTED TO MAKE A HOVER OVER EXPLANATION)
        tk.Button(top, text = 'OK', command = on_ok).grid(row=4,column=2, padx=10, pady=10)
        tk.Button(top, text = 'Cancel', command = on_cancel).grid(row=4, column=1, padx = 10, pady=10, sticky = 'e')
        var = tk.IntVar(value=1)

        inclusive_filtering_chckbtn = tk.Checkbutton(top, text = 'Inclusive filtering', variable= var)
        inclusive_filtering_chckbtn.grid(row=5, column =1, padx= 10)
    
    def reset(self):
        """Helper function to reset a tkinter treeview filtering"""
        experiments = self.manager.get_experiments('all')
        set_tree_data(self.filtered_tree, experiments, replace = True)
        self.current_filter_var.set('No active filter')

    def process_and_save(self, save_name = None):

        #save_name = self.get_entry_values(entries = save_name_entry) 
        save_name = asksaveasfilename(filetypes = [('Excel files', '*.xlsx'), ('All files', '*.*')], initialfile = 'RAPORT')
        if not save_name:
            return
        
        experiments = get_experiments(self.filtered_tree, manager = self.manager, mode = 'selected')
        self.manager.batch_process_selected_experiments(experiment_collectible = experiments, save_name = save_name)

        messagebox.showinfo(title = 'Save', 
                            message = f'Saved {save_name} successfully!')
        '''
        if save_name is None:
            top = tk.Toplevel(self)
            top.title('No save name!')
            tk.Label(top, text = 'No save name. Please insert it below').pack()
            save_name_entry = tk.Entry(top)
            save_name_entry.pack()
            tk.Button(top, text = 'OK', command = save).pack()
        '''

    def create_new_project(self):
        list_of_experiments = self.loader.choose_files()
        self.manager.set_experiments(list_of_experiments)
        set_tree_data(tree_item = self.filtered_tree, experiment_list = self.manager.get_experiments('all'), replace = True)
        messagebox.showinfo('Loaded', 'Data loaded successfully!')

    def append_files(self):
        list_of_experiments = self.loader.choose_files()
        self.manager.append_experiments(list_of_experiments)
        set_tree_data(tree_item= self.filtered_tree, experiment_list = list_of_experiments, replace = False)

    def copy_experiment(self):
        experiments = get_experiments(self.filtered_tree, self.manager, 'selected')
        list_of_copies = []
        for experiment in experiments:
            experiment_copy = copy.deepcopy(experiment)

            new_id = self.loader.update_counter(+1)
            setattr(experiment_copy, 'id', new_id)
            self.manager.append_experiments(experiment_copy)
            list_of_copies.append(experiment_copy)

        set_tree_data(tree_item= self.filtered_tree, experiment_list = list_of_copies, replace = False)

    def delete_selected(self):
        experiments = get_experiments(self.filtered_tree, self.manager, 'selected')
        self.manager.delete_experiments(experiments)
        for experiment in experiments:
            id = str(experiment.id)
            self.filtered_tree.delete(id)
        delete_empty_tag_nodes(self.filtered_tree)
            

    def get_entry_values(self, entries:tk.Entry | list[tk.Entry]):

        results = []
        if isinstance(entries, tk.Entry):
            entries = [entries]

        for widget in entries:
            val = widget.get()
            if val in ("", "<choose an object>"):
                results.append(None)
            else:
                results.append(val)
            
        if len(results) > 1:
            return results
        
        return results[0] 
    
    def process_chronop(self):
        experiments = self.manager.filter(object_type = Chronoamperometry)
        results = []
        for exp in experiments:
            #interactive picking of current
            exp.get_current_at_time(-1)

            #the function doesn't return cause it's based on a click. Access the attributes )WIP)
            results.append((exp.time, exp.potential*1000, exp.current_density*1000))
        print(results)
        df = pd.DataFrame(results)
        self.tmp.append(df)

    
    def join(self):
        x = pd.concat(self.tmp,axis=1)
        x.to_excel('FINAL.xlsx', engine = 'openpyxl')

    
    def inspect(self, event):
        x = get_experiments(self.filtered_tree, self.manager, 'selected')[0]
        dict_to_show = x.get_essentials()

        top = tk.Toplevel(self)
        top.title("Experiment Metadata")

        entries = {}  # keep references to Entry widgets

        tk.Label(top, text = 'Parameter', font = 'TkDefaultFont 13 bold').grid(row=0, column = 0, padx = 5, pady = 10, sticky='w')
        tk.Label(top, text = 'Value', font = 'TkDefaultFont 13 bold').grid(row=0, column =1, padx =5, pady=10, sticky = 'w')

        for i, (widget_label, (value, widget_type, data_type, attr_name)) in enumerate(dict_to_show.items(), start = 1):
            tk.Label(top, text=str(widget_label)).grid(row=i, column=0, sticky="w", padx=5, pady=2)


            if widget_type == 'ENTRY':

                entry = tk.Entry(top)
                entry.insert(0, str(value))   # pre-fill with current value
                entry.grid(row=i, column=1, sticky="w", padx=5, pady=2)
                entries[widget_label] = (entry, data_type, attr_name) # store reference by key
            
            elif widget_type == 'LABEL':

                display_text = value
                if isinstance(value, str) and os.path.exists(value):  # crude "looks like a path"
                    display_text = shorten_path(value, 40)

                label = tk.Label(top, text = str(display_text))
                label.grid(row = i, column = 1, sticky = "w", padx= 5, pady=2)

                if display_text != value:
                    add_tooltip(label, str(value))

        def save_changes():

            for key, (entry, data_type, attr_name) in entries.items():
                str_val = entry.get()
                data_type = data_type
                
                try:
                    if data_type is int:
                        new_val = int(str_val)
                    elif data_type is float:
                        new_val = float(str_val)
                

                except ValueError:
                    tk.messagebox.showerror(
                        "Invalid Input",
                        f"Parameter '{key}' must be {data_type.__name__}, but got: {str_val}"
                    )
                    return  # stop saving on first error
                
                dict_to_show[key] = (new_val, "ENTRY", data_type, attr_name)   # update dict in-place
                
                if key is None:
                    continue
                elif key in x.meta_data:
                    x.meta_data[key] = new_val
                else:
                    setattr(x, attr_name, new_val)
            top.destroy()

        def cancel():
            top.destroy()
            return

        button_frame = tk.Frame(top)
        button_frame.grid(row = len(dict_to_show)+1, column = 0, columnspan = 2, pady=10, sticky = 'we')
        
        cancel_button = tk.Button(button_frame, text = 'Cancel', command = cancel, padx=5, pady=2)
        cancel_button.pack(side = 'right', padx = 10)
        save_button = tk.Button(button_frame, text="Save", command=save_changes, padx =5, pady = 2)
        save_button.pack(side = 'right', padx = 10)

 


if __name__ == '__main__':
    app = ExperimentOrchestrator()
    app.mainloop()



