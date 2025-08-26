from openpyxl import Workbook
import os
from tkinter import ttk
from tkinter import messagebox
from matplotlib import pyplot as plt
from typing import Literal

def create_empty_excel(file_name: str):
    if not os.path.exists(file_name):
        wb = Workbook()
        ws = wb.active
        ws.title = "temp"  # dummy sheet
        wb.save(file_name+'.xlsx')

def ask_user(prompt_string, input_types, *format_args, **format_kwargs):
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

def update_tag_nodes(tree_item:ttk.Treeview, experiment_list):
    
    tag_nodes = getattr(tree_item, 'tag_nodes', {})
    for exp in experiment_list:
        tag = exp.tag if hasattr(exp, 'tag') else 'Untagged'
        if tag not in tag_nodes:
            tag_node = tree_item.insert('', 'end', text=tag, open=True, values = (None, None, None))  # parent node for this tag
            tag_nodes[tag] = tag_node
    
    setattr(tree_item, 'tag_nodes', tag_nodes)
    return tag_nodes


def set_tree_data(tree_item:ttk.Treeview, experiment_list, replace: bool = False):
    
    if replace:
        experiments = list(get_all_treeview_nodes(tree_item, ''))
        tree_item.delete(*experiments)
        setattr(tree_item, 'tag_nodes', {})

    # Create mapping tag -> tree node ID
    tag_nodes = update_tag_nodes(tree_item, experiment_list)

    # Now insert each experiment under the correct tag node
    for exp in experiment_list:
        filename = os.path.basename(exp.file_path)
        tag = exp.tag if hasattr(exp, 'tag') else 'Untagged'
        parent_node = tag_nodes[tag]
        
        tree_item.insert(
            parent_node, 'end',
            text=filename,
            iid=exp.id,  # unique ID for the row
            open=False,
            values=(exp.id, None, None)
        )

        if not hasattr(exp, 'data_list'):
            exp.load_data()
        #    exp.process_data()
            
        #for i, curve in enumerate(exp.processed_data):
        #    curve_id = str(exp.id) + '.' + str(i)
        #    curve_node = tree_item.insert(path_node, 'end', text = f'Curve {i}', iid = curve_id, open = False, values = (exp.id, i, None))
            
        #    for column in curve.columns:
        #        column_node = tree_item.insert(curve_node, 'end', text = column, values = (exp.id, i, column))


def get_all_treeview_nodes(tkinter_treeeview: ttk.Treeview, parent = ''):
    '''Recursively yield all items under the given parent'''

    for child in tkinter_treeeview.get_children(parent):
        yield child

        #this function returns a generator, so it needs to be turned into a list
        yield from get_all_treeview_nodes(tkinter_treeeview, child)


def get_treeview_experiments(tkinter_treeview: ttk.Treeview, mode:str = Literal['selected', 'all']) -> list[dict]:
    '''Helper function to get treeview items and assign them to a universal dictionary with treeview_id, text and values of the item.
    The dictionaries can then be passed to anothe function map_ids_to_experiment to get experiments.
    Args:
    tkinter_treeview: a treeview to get the items from,
    mode: a literal to get either selected experiments or all items in the treeview
    
    Returns:
    a list of dictionaries.'''
    
    
    experiment_dicts = []

    match mode:
        case 'selected':
            list_of_ids = tkinter_treeview.selection()
        case 'all':
            
            #returns a generator from yield
            list_of_ids = get_all_treeview_nodes(tkinter_treeview, '')
            #change to list
            list_of_ids = list(list_of_ids)
            

    if len(list_of_ids) == 0:
        return

    for item_id in list_of_ids:
        
        item = tkinter_treeview.item(item_id)

        #create a dictionary for each treeview item
        experiment_dictionary = {
                                    "treeview_id": item_id,
                                    "text": item['text'],
                                    "values": item['values']
                                    }
        
        experiment_dicts.append(experiment_dictionary)
    
    return experiment_dicts


def map_ids_to_experiments(items: list[dict], manager) -> list[dict]:
    """Function that assigns tkinter treeview dictionary from the function get_treeview_experiments
    and assigns them to another dictionary with experiment, curve number and column, based on the type of parent/child.
    Args:
    items: list of dictionaries with keys treeview_id, text and values
    manager: this function requires filtering by ids, and this is done by an experiment_manager class
    
    Returns:
    experiment_dicts - a list of dictionaires mapping treeview_id to experiments and optionally, the curve numbers/column
    """
    experiment_dicts = []

    for item in items:
        experiment_id, curve_index, column = item['values']
        if experiment_id == 'None':
            continue
        
        experiment = manager.filter_by_id(experiment_id)

        experiment_dictionary = {
                                    "experiment": experiment,
                                    "curve_number": curve_index,
                                    "column": column,
                                    "treeview_id": item["treeview_id"]
                                    }
        
        experiment_dicts.append(experiment_dictionary)

    return experiment_dicts




def get_selection_xy_columns(experiment_dict:dict) -> tuple[str, str]:
    """
    Helper function that takes a dictionary and returns the default_x, default_y attributes of an experiment class,
    each defined differently.

    Args:
        experiment_dict (dict): A single dictionary containing the experiment key mapped to specific experiment.
   
    Returns:
        tuple[str, str] - A tuple containing two strings - default_x and default_y.
    """
    
    print(experiment_dict)
    default_x = getattr(experiment_dict['experiment'], 'default_x')
    #Gets the first x and y columns to verify subsequent experiments.
    if hasattr(experiment_dict['experiment'], 'Ru') and 'E vs RHE [V]' in default_x:
        setattr(experiment_dict['experiment'], 'default_x', 'E_iR vs RHE [V]')
        default_x = 'E_iR vs RHE [V]'
    
    default_y = experiment_dict['column']
    if default_y == 'None':
        default_y = getattr(experiment_dict['experiment'], 'default_y')

    return default_x, default_y
    
    #The selection tuple is made up of strings -> need to convert them or check for strings (e.g None in get_data())



def validate_selection_compatibility(experiment_dicts, first_x, first_y):

    #This ensures different behavior dependent on level
    for experiment_dict in experiment_dicts:

        experiment = experiment_dict['experiment']
        curve_number = experiment_dict['curve_number']
        
        x_column = getattr(experiment, 'default_x')
        y_column = experiment_dict['column']
        
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
    

def plot_experiment(experiment_dict, ax, canvas, x_column, y_column, **kwargs):

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
    experiment = experiment_dict['experiment']
    curve_number = experiment_dict['curve_number']
    name = getattr(experiment, 'file_path')

    data = experiment.get_data(index = curve_number, data_type = 'processed_data')

    for curve in data:
            x = curve[x_column]
            y = curve[y_column]
            
            plt.ticklabel_format(axis='y', style = 'sci', scilimits=(-2,3))

            if type(experiment).__name__  == 'EIS':
                line_plot = ax.scatter(x,y, label = f'{os.path.basename(name)}', alpha = kwargs.get('alpha', 1.0))
                set_equal_axis_limits(ax)
            else:
                line_plot, = ax.plot(x,y, label = f'{os.path.basename(name)}', alpha = kwargs.get('alpha', 1.0))
            plots.append(line_plot)

    ax.set_xlabel(x_column)
    ax.set_ylabel(y_column)
    ax.legend()
    canvas.draw()
    return plots


def clear_plot(ax: plt.Axes):
    ax.clear()

def get_tree_level(tkinter_tree ,item_id, get_parent_name:bool = False):

    final_parent_name = []

    level = 0
    parent = tkinter_tree.parent(item_id)
    parent_name = tkinter_tree.item(parent, 'text')
    final_parent_name.append(parent_name)

    while parent:
        level += 1
        
        parent = tkinter_tree.parent(parent)
        parent_name = tkinter_tree.item(parent, 'text')
        final_parent_name.append(parent_name)

    if get_parent_name:

        final_parent_name.reverse()
        final = ".".join(final_parent_name)
        return level, final
    
    else:
        return level

    
