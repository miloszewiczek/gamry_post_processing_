from core import ExperimentLoader, ExperimentManager, VisualizerWindow
import json
from app_config import messages, settings
from experiments import *
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import os
from tkinter import messagebox
from utilities.other import *
from functions.functions import calculate_slopes
from tkinter.filedialog import asksaveasfilename
from tafel_window import tafel_window

class ExperimentOrchestrator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Miloszs app for electrochemical data!')

        self.loader = ExperimentLoader()
        self.manager = ExperimentManager()
        self.tmp = []
        
        self._setup_gui()
        

    def _setup_gui(self):
  
        #CONFIGURE FILTERING TREE SIZE
        self.columnconfigure(0, minsize=300, weight = 1)
        self.rowconfigure(0, weight=1)


        #FILTERING TREE
        self.filtering_tree_frame = tk.Frame(self)
        self.filtering_tree_frame.grid(row=0, column = 0, sticky = 'nsew')
        self.filtered_tree = ttk.Treeview(self.filtering_tree_frame)
        self.filtered_tree.heading('#0', text ='Type')
        self.filtered_tree.column('#0', width = 50)   
        self.filtered_tree.pack(side='left', fill = tk.BOTH, expand = 1)
        vsb = ttk.Scrollbar(self.filtering_tree_frame, orient="vertical", command=self.filtered_tree.yview)
        vsb.pack(side='right', fill='y')
        self.filtered_tree.configure(yscrollcommand= vsb.set)
        self.filtered_tree.bind('<Double-Button-1>', self.inspect)



        #BUTTON FRAME
        self.button_frame = tk.Frame(self)
        self.button_frame.grid(row=1, column=0, sticky = 'ew')
        self.load_btn = tk.Button(self.button_frame, text = 'Load', command = self.create_new_project)
        self.load_btn.grid(row = 0, column = 0)

        self.process_btn = tk.Button(self.button_frame, text = 'Process selected', command = self.process_selected)
        self.process_btn.grid(row=0, column = 1)

        self.filter_btn = tk.Button(self.button_frame, text = 'Filter', command = self.filter_experiments)
        self.filter_btn.grid(row = 0, column = 2)

        self.process_all_btn = tk.Button(self.button_frame, text = 'Process All', command = self.process_all)
        self.process_all_btn.grid(row=0, column =3 )

        tk.Button(self.button_frame, text = 'Save all', command = self.process_and_save).grid(row=0,column=4)
        tk.Button(self.button_frame, text = 'Append', command = self.append_files).grid(row=1,column=0)


        #PREVIEW FRAME
        self.preview_frame = tk.Frame(self, width = 50, height = 50)
        self.preview_frame.grid(column=2, row=0, sticky = 'nsew')

            #PREVIEW FIGURE
        self.preview_figure, self.preview_ax = plt.subplots()
        self.preview_figure.set_size_inches(5,5)
        self.preview_ax.set_position((0.15,0.15, 0.75, 0.75))
        self.preview_canvas = FigureCanvasTkAgg(self.preview_figure, self.preview_frame)
        self.preview_canvas.get_tk_widget().pack()
        toolbar = NavigationToolbar2Tk(self.preview_canvas, self.preview_frame)
        toolbar.update()
        self.preview_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        tk.Button(self.preview_frame, text = 'Plot selected', command = self.plot_selected).pack()


        #CONFIG SECTION FRAME
        self.config_frame = tk.LabelFrame(self, bd = 1, text = 'Config', padx = 10, pady=10)
        self.config_frame.grid(column=1, row =0)

            #UNCOMPENSATED RESISTANCE
        tk.Label(self.config_frame,text = 'Uncompensated resistance [Ohm]').grid(column=0, row =0, sticky = 'w')
        self.Ru_var = tk.StringVar(value=0)
        self.Ru_cbox = ttk.Combobox(self.config_frame, textvariable = self.Ru_var)
        self.Ru_cbox.grid(column = 1, row =0)

            #GEOMETRIC AREA
        tk.Label(self.config_frame, text = 'Geometric Area [cm2]', justify='left').grid(column=0, row = 1, sticky = 'w')
        self.geometrical_area_var = tk.StringVar(value = '0.07069')
        self.geometrical_area_entry = ttk.Combobox(self.config_frame, textvariable = self.geometrical_area_var)
        self.geometrical_area_entry['values'] = ('0.07069)', 
                                               '0.007854', 
                                               '0.196', 
                                               '0.08')
        self.geometrical_area_entry.grid(column=1, row =1)
        self.apply_Ru_btn = tk.Button(self.config_frame, 
                                      text = 'Apply to all', 
                                      command = self.apply_attr_to_all)
        self.apply_Ru_btn.grid(column=0, row =3)

            #REFERENCE POTENTIAL
        tk.Label(self.config_frame, text = 'Reference Electrode potential [V]', justify = 'left').grid(column=0, row = 2, sticky = 'w')
        self.reference_electrode_var = tk.DoubleVar(value = 0.21)
        self.reference_electrode_entry = ttk.Combobox(self.config_frame, textvariable= self.reference_electrode_var)
        self.reference_electrode_entry['values'] = ('0.21', '0.255')
        self.reference_electrode_entry.grid(column=1, row = 2)

        #CDL SLIDER GUI

        #self.cdl_slider_button = tk.Button(self.preview_frame, text='CDL Slider', command = self.cdl_slider)
        #self.cdl_slider_button.pack()

        #TAFEL BTN
        tk.Button(self.button_frame, text = 'Calculate Tafel', command = self.tafel_plot).grid(row=2, column=0)


        #INSPECTOR FRAME (WIP)
        self.inspector_frame = tk.LabelFrame(text = 'Object Inspector')
        self.inspector_frame.grid(row=1, column = 1)
        self.inspect_btn = tk.Button(self.inspector_frame, text = 'inspect', command = self.print_experiment_data)
        self.inspect_btn.grid(row=0,column=0)


        #CHRONOP_BTN (TEMPRORARY)
        tk.Button(self.button_frame, text = 'Process chronop', command = self.process_chronop).grid(row=3, column =0)
        tk.Button(self.button_frame, text = 'Join', command = self.join).grid(row=3, column = 1)

    
    def print_experiment_data(self):
        experiment = self.filtered_tree.selection()[0]
        exps = map_ids_to_experiments(experiment, self.manager)
        exp = exps[0]['experiment'].data_listex
        print(len(exp))

    def tafel_plot(self):
        experiment = self.manager.filter(object_type=LinearVoltammetry)
        tafel_w = tafel_window(self)
        set_tree_data(tafel_w.data_treeview, experiment)
        

    def apply_attr_to_all(self):
            
        experiments = get_experiments(self.filtered_tree, self.manager, 'all')
        Ru_value = float(self.Ru_var.get())
        geometrical_area = float(self.geometrical_area_var.get())
        reference_potential = float(self.reference_electrode_var.get())

        for experiment in experiments:
    
            setattr(experiment, 'Ru', Ru_value)
            setattr(experiment, 'geometrical_area', geometrical_area)
            setattr(experiment, 'reference_potential', reference_potential)

            experiment.process_data()
    
    def cdl_slider(self):
        from slider import InteractivePlotApp
        d = self.manager.filter(object_type = Voltammetry)
        window = InteractivePlotApp(self)
        set_tree_data(window.data_treeview, d)

    def process_selected(self):
        
        #get selected experiments 
        for experiment in get_experiments(self.filtered_tree, self.manager, 'selected'):
            experiment.process_data()

    def process_all(self):

        #get all experiments
        for experiment in get_experiments(self.filtered_tree, self.manager, 'all'):
            experiment.process_data()


    def plot_selected(self):

        #clear the preview plot
        clear_plot(self.preview_ax)
        

        experiment_mappers = get_mappers(self.filtered_tree, self.manager, 'selected')
        if experiment_mappers is None:
            return
        
        #get first_x and first_y attributes of the first experiment for further validation
        first_x, first_y = get_selection_xy_columns(experiment_mappers[0])
        print(first_x)

        #validating the column names, returns an error window if they are different
        validate_selection_compatibility(experiment_mappers = experiment_mappers, first_x= first_x, first_y = first_y)
        for experiment_dict in experiment_mappers:
            plot_experiment(experiment_dict, self.preview_ax, self.preview_canvas, first_x, first_y)
    


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

        for i, (widget_label, (value, widget_type, data_type, attr_name)) in enumerate(dict_to_show.items()):
            tk.Label(top, text=str(widget_label)).grid(row=i, column=0, sticky="w", padx=5, pady=2)


            if widget_type == 'ENTRY':

                entry = tk.Entry(top)
                entry.insert(0, str(value))   # pre-fill with current value
                entry.grid(row=i, column=1, sticky="we", padx=5, pady=2)
                entries[widget_label] = (entry, data_type, attr_name) # store reference by key
            
            elif widget_type == 'LABEL':

                display_text = value
                if isinstance(value, str) and os.path.exists(value):  # crude "looks like a path"
                    display_text = shorten_path(value, 40)

                label = tk.Label(top, text = str(display_text))
                label.grid(row = i, column = 1, sticky = "we", padx= 5, pady=2)

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

        save_button = tk.Button(top, text="Save", command=save_changes)
        save_button.grid(row=len(dict_to_show), column=0, columnspan=2, pady=10)

if __name__ == '__main__':
    app = ExperimentOrchestrator()
    app.mainloop()



