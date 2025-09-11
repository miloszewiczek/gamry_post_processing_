from openpyxl import Workbook
import os
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from matplotlib import pyplot as plt
from typing import Literal, Any
from dataclasses import dataclass
from experiments import Experiment


@dataclass
class TreeNode:
    treeview_id: str
    text: str
    node_type: str
    experiments: Experiment | list[Experiment]
    other_info: Any


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
        

def set_tree_data(tree:ttk.Treeview, experiment_list: list | Experiment, replace: bool = False):
    
    if replace:
        experiments = list(get_all_treeview_nodes(tree, ''))
        tree.delete(*experiments)
        setattr(tree, 'tag_nodes', {})


    # Create mapping tag -> tree node ID
    tag_nodes = update_tag_nodes(tree, experiment_list, mode = 'tag')

    # Now insert each experiment under the correct tag node

    for exp in experiment_list:
        filename = os.path.basename(exp.file_path)
        tag = exp.tag if hasattr(exp, 'tag') else 'Untagged'

        parent_node = tag_nodes[tag]
        
        tree.insert(
            parent_node, 'end',
            text=filename,
            iid=exp.id,  # unique ID for the row
            open=False,
            values=('Experiment', exp.id, None)
        )

        if not hasattr(exp, 'data_list'):
            exp.load_data()


        #    exp.process_data()
            
        #for i, curve in enumerate(exp.processed_data):
        #    curve_id = str(exp.id) + '.' + str(i)
        #    curve_node = tree_item.insert(path_node, 'end', text = f'Curve {i}', iid = curve_id, open = False, values = (exp.id, i, None))
            
        #    for column in curve.columns:
        #        column_node = tree_item.insert(curve_node, 'end', text = column, values = (exp.id, i, column))


def get_all_treeview_nodes(tree: ttk.Treeview, parent = ''):
    '''Recursively yield all items under the given parent'''

    for child in tree.get_children(parent):
        yield child

        #this function returns a generator, so it needs to be turned into a list
        yield from get_all_treeview_nodes(tree, child)


def create_nodes_from_ids(tree: ttk.Treeview, collection_of_ids: tuple|list, manager) -> list[dict]:
    """Helper function to create dictionaries from a treeview and a collection of ids."""

    tree_nodes = []
    for item_id in collection_of_ids:
        
        item = tree.item(item_id)
        node_type, exp_id, other_info = item['values']
        
        if node_type == 'Node':
            experiment_ids = tree.get_children(item_id)
            experiment_nodes = create_nodes_from_ids(tree, experiment_ids, manager)
            experiments = get_experiments_from_nodes(experiment_nodes)

        
        elif node_type == 'Experiment':
            experiments = manager.filter_by_id(item_id)

        #create a dictionary for each treeview item
        node = TreeNode(treeview_id = item_id,
                        text = item['text'],
                        node_type = node_type,
                        experiments = experiments,
                        other_info = other_info)

        tree_nodes.append(node)
        
    return tree_nodes

def get_treeview_nodes(tree: ttk.Treeview, manager, mode:str = Literal['selected', 'all'], ) -> list[dict]:
    '''Helper function to get treeview items and assign them to a universal dictionary with treeview_id, text and values of the item.
    The dictionaries can then be passed to anothe function map_ids_to_experiment to get experiments.
    Args:
    tree: a treeview to get the items from,
    mode: a literal to get either selected experiments or all items in the treeview
    
    Returns:
    a list of dictionaries.'''

    match mode:

        case 'selected':
            list_of_ids = tree.selection()

        case 'all':
            
            #returns a generator from yield
            list_of_ids = get_all_treeview_nodes(tree, '')
            #change to list
            list_of_ids = list(list_of_ids)

    #error check
    if len(list_of_ids) == 0:
        return
    
    #create dicts from tkinter values
    experiment_nodes = create_nodes_from_ids(tree, list_of_ids, manager)
    
    return experiment_nodes


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



def validate_selection_compatibility(nodes, first_x, first_y):

    #This ensures different behavior dependent on level
    for node in nodes:

        experiment = node.experiments
        
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
    

def plot_experiment(node, ax, canvas, x_column, y_column, **kwargs):

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
    experiment = node.experiments
    name = getattr(experiment, 'file_path')

    data = experiment.get_data(index = None, data_type = 'processed_data')

    for curve in data:
            x = curve[x_column]
            y = curve[y_column]
            
            plt.ticklabel_format(axis='y', style = 'sci', scilimits=(-2,3))

            if type(experiment).__name__  == 'EIS':
                line_plot = ax.scatter(x,y, label = f'{os.path.basename(name)}', alpha = kwargs.get('alpha', 1.0))
                set_equal_axis_limits(ax)
            else:
                line_plot, = ax.plot(x,y, label = f'{os.path.basename(name)}', alpha = kwargs.get('alpha', 1.0))
            
            setattr(line_plot, 'experiment', experiment)
            plots.append(line_plot)

    #ax.legend()
    canvas.draw()
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


