from experiments import *
from tkinter.filedialog import asksaveasfile, asksaveasfilename, askopenfile
import copy
from core import ExperimentLoader, ExperimentManager
import json
import tkinter as tk
from tkinter import ttk
from .treenode import TreeNode
from datetime import datetime
import getpass


def filter_experiments(manager, parent=None):
    """
    Open a modal dialog, let the user pick filter values, and return a list
    of experiments matching the filter. Returns an empty list if cancelled or nothing matches.
    """
    result = []   # will hold returned experiments

    # helper to read entries
    def get_entry_values():
        name = name_filter_entry.get().strip()
        cycle = cycle_filter_entry.get().strip()
        obj = object_filter_combobox.get()
        # convert empty strings to None so manager.filter can treat missing args properly
        return (name or None, cycle or None, None if obj == '<choose an object>' else obj)

    def on_ok():
        nonlocal result
        name_filter, cycle_filter, object_type_filter = get_entry_values()
        # call manager.filter — adapt args to how your manager.filter wants them
        experiments = manager.filter(
            name=name_filter,
            cycle=cycle_filter,
            object_type=object_type_filter,
            inclusive=var.get()
        )
        result = list(experiments) or []
        top.destroy()

    def on_cancel():
        # leave result as empty list
        top.destroy()

    # Build modal dialog
    top = tk.Toplevel(parent) if parent is not None else tk.Toplevel()
    top.title("Filtering")
    top.transient(parent)            # keep it on top of parent
    top.grab_set()                   # make it modal (block input to other windows)
    # layout
    tk.Label(top, text='Please input the filtering keys.').grid(row=0, column=0, columnspan=2, pady=10, sticky='w')

    tk.Label(top, text='Name filter:').grid(row=1, column=0, sticky='w', padx=10)
    name_filter_entry = tk.Entry(top)
    name_filter_entry.grid(row=1, column=1, sticky='we')

    tk.Label(top, text='Cycle filter:').grid(row=2, column=0, sticky='w', padx=10)
    cycle_filter_entry = tk.Entry(top)
    cycle_filter_entry.grid(row=2, column=1, sticky='we')

    tk.Label(top, text='Object filter:').grid(row=3, column=0, sticky='w', padx=10)
    object_filter_combobox = ttk.Combobox(top, values=manager.get_unique_experiments())
    object_filter_combobox.grid(row=3, column=1, sticky='we')
    object_filter_combobox.set('<choose an object>')

    var = tk.IntVar(value=1)
    inclusive_filtering_chckbtn = tk.Checkbutton(top, text='Inclusive filtering', variable=var)
    inclusive_filtering_chckbtn.grid(row=4, column=1, padx=10, sticky='w')

    btn_frame = tk.Frame(top)
    btn_frame.grid(row=5, column=0, columnspan=2, pady=8)
    tk.Button(btn_frame, text='OK', command=on_ok).pack(side='right', padx=6)
    tk.Button(btn_frame, text='Cancel', command=on_cancel).pack(side='right')

    # Make dialog keyboard-friendly
    name_filter_entry.focus_set()
    top.bind('<Return>', lambda e: on_ok())
    top.bind('<Escape>', lambda e: on_cancel())

    # Wait here until the window is destroyed (OK or Cancel)
    parent.wait_window(top) if parent is not None else top.wait_window()

    # When we get here, the dialog was closed and `result` is set
    return result
    

def process(tree:ttk.Treeview, manager:ExperimentManager, selection_mode: Literal['selected','all'] = 'selected') -> None:

    nodes = get_treeview_nodes(tree, manager, mode = selection_mode)

    if selection_mode == 'selected':
        is_both_type_of_nodes = check_nodes_if_selected(nodes)
        if is_both_type_of_nodes:
            result = messagebox.askyesno('Tag end Experiment nodes selected', 'Both types of nodes were selected.\nIf you want to process all Experiments, press yes. Otherwise, select a single Experiment node and try again.')
    exps = get_experiments_from_nodes(nodes)
    for exp in exps:
        exp.process_data()
    for node in nodes:
        tree.item(node.treeview_id, tags = ('processed'))
    

def process_and_save(manager, experiments):

    #save_name = self.get_entry_values(entries = save_name_entry) 
    save_name = asksaveasfilename(filetypes = [('Excel files', '*.xlsx'), ('All files', '*.*')], initialfile = 'RAPORT')
    if not save_name:
        return
    
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

def load(loader:ExperimentLoader, manager:ExperimentManager, from_ = Literal['folder', 'files'], mode = Literal['replace','append']):
    
    match from_:
        case 'folder':
            dict_of_experiments = loader.choose_folder()
        case 'files':
            dict_of_experiments = loader.choose_files()

    match mode:
        case 'replace':
            manager.set_experiments(dict_of_experiments)
        case 'append':
            manager.append_experiments(dict_of_experiments)

    return dict_of_experiments

def copy_experiment(loader:ExperimentLoader, tree: ttk.Treeview, manager:ExperimentManager):
    
    nodes = get_treeview_nodes(tree, manager, 'selected')
    experiments = get_experiments_from_nodes(nodes)
    list_of_copies = []
    

    for experiment in experiments:
        print(experiment.id)
        experiment_copy = copy.deepcopy(experiment)

        new_id = loader.get_counter()

        setattr(experiment_copy, 'id', new_id)
        manager.append_experiments(experiment_copy)
        list_of_copies.append(experiment_copy)

        loader.update_counter(+1)

    set_tree_data(tree = tree, experiment_list = list_of_copies, replace = False)


def delete_selected(tree:ttk.Treeview, manager:ExperimentManager):
    nodes = get_treeview_nodes(tree, manager, 'selected')
    experiments = get_experiments_from_nodes(nodes)
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

def process_chronop(manager:ExperimentManager):
    experiments = manager.filter(object_type = Chronoamperometry)
    results = []
    for exp in experiments:
        #interactive picking of current
        exp.get_current_at_time(-1)

        #the function doesn't return cause it's based on a click. Access the attributes )WIP)
        results.append((exp.time, exp.potential*1000, exp.current_density*1000))
    print(results)
    df = pd.DataFrame(results)
    

def inspect_wrapper(event, tree:ttk.Treeview, manager:ExperimentManager):
   
    #this returns a list, however get_info needs a list
    node_to_inspect = get_treeview_nodes(tree, manager, 'selected' )[0]
    node_type  = get_info_from_nodes(node_to_inspect, 'node_type')
    print(node_to_inspect.treeview_id)
    match node_type:
        case 'Node':
            inspect_node(node_to_inspect)
        
        case 'Experiment':
            #grab first one
            exp = get_experiments_from_nodes(node_to_inspect)[0]
            inspect_experiment(exp)



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


def plot_selected(controller, ax, canvas):

    #clear the preview plot
    clear_plot(ax)
    
    experiments = controller.get_experiments('selection')
    if experiments is None:
        return
    
    #get first_x and first_y attributes of the first experiment for further validation
    first_experiment = experiments[0]
    first_x, first_y = getattr(first_experiment, 'default_x'), getattr(first_experiment, 'default_y')
    print(first_x)

    #validating the column names, returns an error window if they are different
    validate_selection_compatibility(experiments, first_x= first_x, first_y = first_y)
    for experiment in experiments:
        plot_experiment(experiment, ax, canvas, first_x, first_y)




from openpyxl import Workbook
import os
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from matplotlib import pyplot as plt
from typing import Literal, Any
from dataclasses import dataclass
from experiments import Experiment


def create_empty_excel(file_name: str):
    if not os.path.exists(file_name):
        wb = Workbook()
        ws = wb.active
        ws.title = "temp"  # dummy sheet
        wb.save(file_name+'.xlsx')

def ask_user(prompt_string:str, input_types, *format_args, **format_kwargs):
    while True:
        user_input = input(prompt_string.format(*format_args, **format_kwargs))
        
        if not isinstance(input_types, (tuple, list)):  # If one type was provided, change it into tuple
            input_types = (input_types,)

        for input_type in input_types:
            try:
                return input_type(user_input)  # Try to cast the type 
            except ValueError:
                continue  #if ValueError, goes to another type

        print(f"Wrong input type. Expected one of: {', '.join(t.__name__ for t in input_types)}. Try again.")

def update_tag_nodes(tree:ttk.Treeview, experiment_list, mode = Literal['tag', 'folder']):

    tag_nodes = getattr(tree, 'tag_nodes', {})
    for exp in experiment_list:

        if mode == 'folder':
            dir = os.path.dirname(exp.file_path)
            tag = dir
        else:
            tag = getattr(exp, mode) if hasattr(exp, mode) else 'Untagged'
        print(tag)
        if tag not in tag_nodes:
            tag_node = tree.insert('', 'end', text=tag, open=True, values = ('Node', None, None))  # parent node for this tag
            tag_nodes[tag] = tag_node
    
    setattr(tree, 'tag_nodes', tag_nodes)
    return tag_nodes

def create_filepath_nodes(tree: ttk.Treeview, experiment_list):
    
    file_path_nodes = getattr(tree, 'file_path_nodes', [])
    for exp in experiment_list:
        file_path = exp.file_path
        if file_path not in file_path_nodes:
            file_path_nodes.append(file_path)
        else:
            continue

    setattr(tree, 'file_path_nodes', file_path_nodes)


def delete_empty_tag_nodes(tree:ttk.Treeview):
    
    tag_nodes = getattr(tree, 'tag_nodes')
    
    #tag is visible name in treeview, iterating over keys to avoid modifying in place
    for tag in list(tag_nodes.keys()):
        tag_id = tag_nodes[tag]

        #grab children of tag_node - experiment rows
        existing_rows = tree.get_children(tag_id)
        if len(existing_rows) == 0:
            tag_nodes.pop(tag)
            tree.delete(tag_id)

def check_nodes_if_selected(nodes):
    
    list_of_node_types = get_info_from_nodes(nodes, 'node_type')
    if ('Node' in list_of_node_types) and ('Experiment' in list_of_node_types):
        return True
    
    return False

def get_experiments_from_nodes(nodes: list[TreeNode]) -> list[Experiment] | Experiment:

    if not isinstance(nodes, list):
        nodes = [nodes]

    experiments = [node.experiments for node in nodes if node.node_type != 'Node']

    return experiments


def get_info_from_nodes(nodes: list, info: Literal['node_type', 'experiments', 'text', 'other_info', 'treeview_id']):

    if isinstance(nodes, list): #if its a list of nodes

        if isinstance(info, tuple):
            results = [
                tuple(getattr(node, key) for key in info)
                for node in nodes
            ]
        else:
            results = [getattr(node, info) for node in nodes]
 
    else: #if its a single node
        
        if isinstance(info, tuple):
            results =  tuple(getattr(nodes, key) for key in info)
        else:
            results = getattr(nodes, info)

    return results
    

def get_selection_xy_columns(node) -> tuple[str, str]:
    """
    Helper function that takes a dictionary and returns the default_x, default_y attributes of an experiment class,
    each defined differently.

    Args:
        experiment_dict (dict): A single dictionary containing the experiment key mapped to specific experiment.
   
    Returns:
        tuple[str, str] - A tuple containing two strings - default_x and default_y.
    """
    
    
    default_x = getattr(node.experiments, 'default_x')
    #Gets the first x and y columns to verify subsequent experiments.
    if node.experiments.Ru != 0 and 'E vs RHE [V]' in default_x:
        setattr(node.experiments, 'default_x', 'E_iR vs RHE [V]')
        default_x = 'E_iR vs RHE [V]'
    
    default_y = getattr(node.experiments, 'default_y')

    return default_x, default_y
    
    #The selection tuple is made up of strings -> need to convert them or check for strings (e.g None in get_data())



def validate_selection_compatibility(experiments, first_x, first_y):

    #This ensures different behavior dependent on level
    for experiment in experiments:

        x_column = getattr(experiment, 'default_x')
        y_column = getattr(experiment, 'default_y')
        
        if y_column == 'None':
            y_column = getattr(experiment, 'default_y')

        if x_column != first_x or y_column != first_y:
            messagebox.showerror(
            "Incompatible Selection",
            f"Selected items have different data types:\n"
            f"Expected X: {first_x}, Y: {first_y}\n"
            f"Got X: {x_column}, Y: {y_column}"
        )
            return False
    return True
    

def plot_experiment(experiment: Experiment, ax, canvas, x_column, y_column, label = 'file_name', **kwargs):

    def set_equal_axis_limits(ax: plt.Axes):
        """Adjust plot so X and Y have the same limits and scale."""
        x_min, x_max = ax.get_xlim()
        y_min, y_max = ax.get_ylim()
        lim_min = min(x_min, y_min)
        lim_max = max(x_max, y_max)
        ax.set_xlim(lim_min, lim_max)
        ax.set_ylim(lim_min, lim_max)
        return


    plots = []

    try:
        label = getattr(experiment, f'{label}')
    except:
        label = 'Plot'
    
    data = experiment.get_data(index = None, data_type = 'processed_data')

    for curve in data:
            x = curve[x_column]
            y = curve[y_column]
            
            plt.ticklabel_format(axis='y', style = 'sci', scilimits=(-2,3))

            if type(experiment).__name__  == 'EIS':
                line_plot = ax.scatter(x,y, label = label, alpha = kwargs.get('alpha', 1.0))
                set_equal_axis_limits(ax)
            else:
                line_plot, = ax.plot(x,y, label = label, alpha = kwargs.get('alpha', 1.0))
            
            setattr(line_plot, 'experiment', experiment)
            plots.append(line_plot)

    canvas.draw_idle()
    return plots


def clear_plot(ax: plt.Axes):
    ax.clear()


def shorten_path(path: str, max_length: int = 50) -> str:
    """Shorten a file path with '...' in the middle if it's too long."""
    
    if len(path) <= max_length:
        return path
    head, tail = os.path.split(path)
    return os.path.join("...", tail)


def add_tooltip(widget, text: str):
    tooltip = None

    def on_enter(event):
        nonlocal tooltip
        tooltip = tk.Toplevel(widget)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
        tk.Label(tooltip, text=text, background="lightyellow",
                 relief="solid", borderwidth=1, padx=2, pady=2).pack()

    def on_leave(event):
        nonlocal tooltip
        if tooltip:
            tooltip.destroy()
            tooltip = None

    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)


def inspect_node(node, **kwargs):
    
    def process_node(experiments):
        if isinstance(experiments, list):
            for exp in experiments:
                exp.process_data()
        else:
            messagebox.showwarning('Unknown node type', 'I do not know what to do with that type of node...')

    top = tk.Toplevel()
    top.title("Node Information")
    tk.Label(top, text = 'Parameter', font = 'TkDefaultFont 13 bold').grid(row=0, column = 0, padx = 5, pady = 10, sticky='w')
    tk.Label(top, text = 'Value', font = 'TkDefaultFont 13 bold').grid(row=0, column =1, padx =5, pady=10, sticky = 'w')

    node_id = node.treeview_id
    experiments = node.experiments
    text = node.text

    ttk.Label(top, text = 'ID').grid(row = 1, column = 0, padx = 5, pady = 2, sticky = 'w')
    ttk.Label(top, text = node_id).grid(row = 1, column = 1, padx = 5, pady = 2, sticky = 'w')
    ttk.Label(top, text = 'Node name').grid(row = 2, column = 0, padx = 5, pady = 2, sticky = 'w')
    ttk.Label(top, text = text).grid(row=2, column = 1, padx = 5, pady = 2, sticky = 'w')
    ttk.Label(top, text = 'Number of experiments').grid(row=3, column = 0, padx = 5, pady = 2, sticky = 'w')
    ttk.Label(top, text = f'{len(experiments)}').grid(row=3, column = 1, padx = 5, pady = 2, sticky = 'w')

    ttk.Button(top, text = 'Process all', command = lambda: process_node(experiments)).grid(row = 4, column = 0, padx = 5, pady=2)
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

def dump(to_dump: dict[str, tk.Variable]):
    """Function to store configuration data via dictionary to a .json file at user-defined location.
    Args:
    to_dump (dict): a dictionary consisting of a str:tkVariable key:value pairs.
    Returns:
    save_path (str): location of the config file."""
    name = asksaveasfilename(defaultextension='json', initialdir = 'app_config/')
    if name is None:
        return
    #getting the values
    to_dump = {var_name: var.get() for var_name, var in to_dump.items()}
    data = {
        'metadata': {
            'saved_at': datetime.now().isoformat()
        },
        'settings': to_dump
    }
    with open(f'{name}', 'w') as f:
        json.dump(data, f, indent = 4)

    return name

def load_settings(to_update: dict[str, tk.Variable]):
    """A function to load settings from a JSON file and update the values in a dictionary provided by the user.
    Args:
    to_update (dict): a dictionary containing tk.variables"""
    settings_file = json.load(askopenfile('r', filetypes = [('JSON Config File' , '*.json')], initialdir = 'app_config/'))

    keys = to_update.keys()
    for var_name, var_value in settings_file['settings'].items():
        if var_name in keys:
            to_update[var_name].set(var_value)


def merge_curves(lines):
    """A function to merge y-data to obtain an average value e.g. when yo have 3 samples of the same electrode.
    Returns a dataframe containing the average value and standard value calculated row-wise.
    Args:
    lines: a collection of line from a matplotlib ax
    Returns:
    average_std_df (pd.DataFrame): DataFrame containining the average value and standard error"""

    df = pd.DataFrame([line.get_ydata() for line in lines]).T
    df['Average'] = df.mean(axis = 1)
    df['Standard error'] = df.std(axis = 1)
    x = pd.DataFrame([line.get_xdata() for line in lines]).T
    
    final = pd.concat([x, df[['Average','Standard error']]], axis = 1)
    final.to_clipboard()
    
    return final
    

def variable_separation(variable: str, separator: str, final_type = None):
    
    list_of_variables = variable.split(separator)
    list_of_variables = [var.strip() for var in list_of_variables]
    
    if final_type:
        list_of_variables = [final_type(var) for var in list_of_variables]

    return list_of_variables

    

