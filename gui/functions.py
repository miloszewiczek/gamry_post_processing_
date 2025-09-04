from utilities.other import *
from experiments import *
from tkinter.filedialog import asksaveasfile, asksaveasfilename
import copy


def filter_experiments(tree, manager, variable):

    #ZMIENIĆ FUNCKE FILTER, PO UWZGLĘDNIENIU NOWEJ WERSJI get_entry_and_destroy

    def on_ok():
        #collect values
        name_filter, cycle_filter, object_type_filter = get_entry_values(entries= [name_filter_entry, 
                                                                                        cycle_filter_entry,
                                                                                        object_filter_combobx])
    
        #run filtering
        experiments = manager.filter(name = name_filter, 
                                        cycle = cycle_filter, 
                                        object_type= object_type_filter,
                                        inclusive = var.get())
    
        #update tree
        set_tree_data(tree_item = tree, experiment_list = experiments, replace = True)

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

        variable.set(f'Active filter: {desc}')



    def on_cancel():

        top.destroy()
        return

    #create a new window with filter entries
    top = tk.Toplevel()
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
    object_filter_combobx = ttk.Combobox(top, values = manager.get_unique_experiments()) 
    object_filter_combobx.grid(row=3, column = 1, sticky = 'we')
    object_filter_combobx.set('<choose an object>')

    #ADD BIND METHOD OVERALL! (WANTED TO MAKE A HOVER OVER EXPLANATION)
    tk.Button(top, text = 'OK', command = on_ok).grid(row=4,column=2, padx=10, pady=10)
    tk.Button(top, text = 'Cancel', command = on_cancel).grid(row=4, column=1, padx = 10, pady=10, sticky = 'e')
    var = tk.IntVar(value=1)

    inclusive_filtering_chckbtn = tk.Checkbutton(top, text = 'Inclusive filtering', variable= var)
    inclusive_filtering_chckbtn.grid(row=5, column =1, padx= 10)
    
def reset(tree, manager):
    """Helper function to reset a tkinter treeview filtering"""
    experiments = manager.get_experiments('all')
    set_tree_data(tree, experiments, replace = True)
    #current_filter_var.set('No active filter')

def process_and_save(tree, manager, save_name = None):

    #save_name = self.get_entry_values(entries = save_name_entry) 
    save_name = asksaveasfilename(filetypes = [('Excel files', '*.xlsx'), ('All files', '*.*')], initialfile = 'RAPORT')
    if not save_name:
        return
    
    experiments = get_experiments(tree, manager, mode = 'selected', output = 'experiments')
    manager.batch_process_selected_experiments(experiment_collectible = experiments, save_name = save_name)

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

def create_new_project(loader, tree, manager):
    list_of_experiments = loader.choose_files()
    manager.set_experiments(list_of_experiments)
    set_tree_data(tree_item = tree, experiment_list = manager.get_experiments('all'), replace = True)
    messagebox.showinfo('Loaded', 'Data loaded successfully!')

def append_files(loader,tree, manager):
    list_of_experiments = loader.choose_files()
    manager.append_experiments(list_of_experiments)
    set_tree_data(tree_item= tree, experiment_list = list_of_experiments, replace = False)

def copy_experiment(loader,tree, manager):
    experiments = get_experiments(tree, manager, 'selected', output = 'experiments')
    list_of_copies = []
    for experiment in experiments:
        experiment_copy = copy.deepcopy(experiment)

        new_id = loader.update_counter(+1)
        setattr(experiment_copy, 'id', new_id)
        manager.append_experiments(experiment_copy)
        list_of_copies.append(experiment_copy)

    set_tree_data(tree_item= tree, experiment_list = list_of_copies, replace = False)


def delete_selected(tree, manager):
    experiments = get_experiments(tree, manager, 'selected', output = 'experiments')
    manager.delete_experiments(experiments)
    for experiment in experiments:
        id = str(experiment.id)
        tree.delete(id)
    delete_empty_tag_nodes(tree)
        
def get_entry_values(entries:tk.Entry | list[tk.Entry]):

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

def process_chronop(manager):
    experiments = manager.filter(object_type = Chronoamperometry)
    results = []
    for exp in experiments:
        #interactive picking of current
        exp.get_current_at_time(-1)

        #the function doesn't return cause it's based on a click. Access the attributes )WIP)
        results.append((exp.time, exp.potential*1000, exp.current_density*1000))
    print(results)
    df = pd.DataFrame(results)
    

def join(self):
    x = pd.concat(self.tmp,axis=1)
    x.to_excel('FINAL.xlsx', engine = 'openpyxl')


def inspect_wrapper(event, tree, manager):
    object_to_inspect = get_experiments(tree, manager, 'selected', output = 'mappers')
    #need to add a function which validates whether it's a node or list of experiments
    #to do that I will need to change the get_experiments functino to only yield experiments
    #Possibly introduce get_node()?
    
    if isinstance(object_to_inspect, str):
        node_id = object_to_inspect
        inspect_node(tree, node_id, manager = manager)

    elif isinstance(object_to_inspect, list): #otherwise it's a list of experiments
        experiment = get_experiments(tree, manager, 'selected', output = 'experiments')[0]
        inspect_experiment(experiment)

    else:
        print('I do not know what to do with that item. It is neither a node no a list of experiments')

def inspect_node(tree:ttk.Treeview, node_id: str, **kwargs):
    
    def process_node(children_ids):
        experiments = get_experiments_by_tree_ids(tree, kwargs['manager'], children_ids)
        for exp in experiments:
            exp.process_data()

    top = tk.Toplevel()
    top.title("Node Information")
    tk.Label(top, text = 'Parameter', font = 'TkDefaultFont 13 bold').grid(row=0, column = 0, padx = 5, pady = 10, sticky='w')
    tk.Label(top, text = 'Value', font = 'TkDefaultFont 13 bold').grid(row=0, column =1, padx =5, pady=10, sticky = 'w')

    text, children = tree.item(node_id)['text'], tree.get_children(node_id)
    ttk.Label(top, text = 'ID').grid(row = 1, column = 0, padx = 5, pady = 2, sticky = 'w')
    ttk.Label(top, text = node_id).grid(row = 1, column = 1, padx = 5, pady = 2, sticky = 'w')
    ttk.Label(top, text = 'Node name').grid(row = 2, column = 0, padx = 5, pady = 2, sticky = 'w')
    ttk.Label(top, text = text).grid(row=2, column = 1, padx = 5, pady = 2, sticky = 'w')
    ttk.Label(top, text = 'Number of experiments').grid(row=3, column = 0, padx = 5, pady = 2, sticky = 'w')
    ttk.Label(top, text = f'{len(children)}').grid(row=3, column = 1, padx = 5, pady = 2, sticky = 'w')

    ttk.Button(top, text = 'Process all', command = lambda: process_node(children)).grid(row = 4, column = 0, padx = 5, pady=2)
    ttk.Button(top, text = 'Cancel', command = top.destroy).grid(row = 4, column = 1, padx = 5, pady =2)


def inspect_experiment(experiment: Experiment):
    dict_to_show = experiment.get_essentials()

    top = tk.Toplevel()
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
            elif key in experiment.meta_data:
                experiment.meta_data[key] = new_val
            else:
                setattr(experiment, attr_name, new_val)
        top.destroy()

    def cancel():
        top.destroy()
        return
    
    def save_and_process():
        save_changes()
        experiment.process_data()


    button_frame = tk.Frame(top)
    button_frame.grid(row = len(dict_to_show)+1, column = 0, columnspan = 2, pady=10, sticky = 'we')
    
    cancel_button = tk.Button(button_frame, text = 'Cancel', command = cancel, padx=5, pady=2)
    cancel_button.pack(side = 'right', padx = 10)
    save_button = tk.Button(button_frame, text="Save", command=save_changes, padx =5, pady = 2)
    save_button.pack(side = 'right', padx = 10)

    save_and_process_button = tk.Button(button_frame, text = 'Save and process', command = save_and_process, padx = 5, pady = 2)
    save_and_process_button.pack(side = 'right', padx = 10)


def plot_selected(tree, manager, ax, canvas):

    #clear the preview plot
    clear_plot(ax)
    

    experiment_mappers = get_experiments(tree, manager, 'selected', output = 'mappers')
    if experiment_mappers is None:
        return
    
    #get first_x and first_y attributes of the first experiment for further validation
    first_x, first_y = get_selection_xy_columns(experiment_mappers[0])
    print(first_x)

    #validating the column names, returns an error window if they are different
    validate_selection_compatibility(experiment_mappers = experiment_mappers, first_x= first_x, first_y = first_y)
    for experiment_dict in experiment_mappers:
        plot_experiment(experiment_dict, ax, canvas, first_x, first_y)


def process(tree, manager, mode: Literal['selected', 'all'] ):
    
    #get selected experiments 
    for experiment in get_experiments(tree, manager, mode, output = 'experiments'):
        experiment.process_data()

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

