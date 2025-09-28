from core import ExperimentManager, ExperimentLoader
import tkinter as tk
from tkinter import ttk
from .treenode import TreeNode
from experiments.base import Experiment
import os
from typing import Literal
from .functions import filter_experiments, inspect_experiment, inspect_node, process_and_save, dump
from copy import deepcopy
from collections import defaultdict
import json

class TreeController:
    def __init__(self, loader: ExperimentLoader, tree: ttk.Treeview, manager: ExperimentManager, nodes = {}):
        self.tree = tree
        self.loader = loader
        self.manager = manager
        self.nodes: dict[str, TreeNode] = nodes  # iid -> TreeNode
        self.selected_all_var = tk.BooleanVar(value = False)
        self.initialize_tree(nodes)

    def initialize_tree(self, nodes: list[Experiment]):
        if nodes:
            for node in nodes:
                self.tree.insert('', 'end', node.id, text = node.file_name)

    def add_node(self, exp_id: str, text: str, experiment, node_type: str, other_info=(None)):
        
        node = TreeNode(exp_id, text, node_type, experiments = experiment, other_info = (1,1,1))
        self.nodes[exp_id] = node
        return node
    
    def update_tree(self):
        for id, item in self.nodes.items():
            print(item.__dict__)
            self.tree.insert('', 'end', iid = item.treeview_id, text = item.experiments.file_path,  values = item.other_info)
    
    def get_selected_nodes(self): 
        return self.tree.selection() 

    def get_id(self, item):
        return getattr(item, 'iid')

    def copy_nodes(self):
        
        experiments = self.get_experiments()
        for exp in experiments:
            copy = deepcopy(exp)
            self.manager._update_counter(+1)
            setattr(copy, 'id', self.manager.counter)
            self.manager.update(copy)
            self.tree.insert("",'end', iid = copy.id, text=os.path.basename(copy.file_path)+ '(C)', values = (1))
    
    def get_nodes(self, ids: Literal['selection', 'all'] = 'selection'):

        if ids == 'selection':
            node_ids = self.tree.selection()
        elif ids == 'all':
            node_ids = self.tree.get_children()
        return node_ids
    
    def get_experiments(self, ids: Literal['selection', 'all'] | int | list[int] = 'selection'):
        
        if isinstance(ids, (int)):
            node_ids = list(ids)
        elif isinstance(ids, str):
            node_ids = self.get_nodes(ids)
        else:
            node_ids = ids

        return [self.manager.get(int(id)) for id in node_ids]

    def delete_nodes(self, ids = None):

        if ids is None:
            ids = self.get_nodes('selection')
        for id in ids:
            self.manager.delete_id(id)
            self.tree.delete(id)


    def get_all_treeview_nodes(self, parent = ''):
        '''Recursively yield all items under the given parent'''

        for child in self.tree.get_children(parent):
            yield child

            #this function returns a generator, so it needs to be turned into a list
            yield from self.get_all_treeview_nodes(child)
            
    def create_nodes_from_ids(self, collection_of_experiments: dict[Experiment]) -> list[dict]:
        """Helper function to create dictionaries from a treeview and a collection of ids."""

        for id, experiment in collection_of_experiments.items():
            self.add_node(id, id, getattr(experiment, 'file_path'), 'experiment', None )


    def load_from_files(self, mode = Literal['replace', 'append']):
        experiments = self.loader.choose_files()
        self._integrate(experiments, mode)

    def load_from_folder(self, mode = Literal['replace', 'append']):
        experiments = self.loader.choose_folder()
        self._integrate(experiments, mode)

    def _integrate(self, experiments, mode):
        if mode == 'replace':
            self.manager.set_experiments(experiments)
        elif mode == 'append':
            self.manager.append_experiments(experiments)
        
        self.refresh_tree()

    def filter(self):

        self.refresh_tree(filter_experiments(self.manager))
    
    def refresh_tree(self, exps = 'all'):
        
        if exps == 'all':
            exps = self.manager.get_all()

        self.tree.delete(*self.tree.get_children())
        for exp in exps:
            
            name = os.path.basename(exp.file_path)
            self.tree.insert("", "end", iid = exp.id, text=name, values = (1))

    def select_or_deselect_all(self):
        '''Method to select all nodes present in the treeview. If all are selected, deselection occurs.
        Args:
        self: TreeController - needs access to the Treeview widget'''

        if self.selected_all_var.get() is True:
            for node in self.get_selected_nodes():
                self.tree.selection_remove(node)    
            self.selected_all_var.set(False)
        else:
            self.tree.selection_add(self.tree.get_children())
            self.selected_all_var.set(True)


    def show_grouped(self, by):
        nodes = self.get_nodes('all')
        experiments = self.get_experiments(nodes)
        self.delete_nodes(nodes)

        grouped = self.group_by(experiments, by)

        def insert(parent, data):
            if isinstance(data, list):  # leaf level → experiments
                for exp in data:
                    self.tree.insert(parent, "end", iid=exp.id, text=os.path.basename(exp.file_path))
            else:  # dict → groups
                for key, sub in data.items():
                    node_id = f"{parent}/{key}"
                    self.tree.insert(parent, "end", iid=node_id, text=str(key), open=True)
                    insert(node_id, sub)

        insert("", grouped)
                

    def group_by(self, experiments, keys:list[str]):
        """Return nested dict grouped by attributes in keys."""
        if not keys:  # no more grouping
            return experiments
        
        grouped = defaultdict(list)
        key = keys[0]
        for exp in experiments:
            val = getattr(exp, key, "Unknown")
            grouped[val].append(exp)

        return {k: self.group_by(v, keys[1:]) for k, v in grouped.items()}
                
    def apply_attr_to_selected(self, tk_var: tk.Variable, var_name: str, mode = 'selection'):
            
        experiments = self.get_experiments(mode)
        attr_to_apply = tk_var.get()
        for experiment in experiments:
            setattr(experiment, var_name, attr_to_apply)
            experiment.process_data()
        
    def apply_multiple(self, attributes:dict, mode = 'selection'):
        
        experiments = self.get_experiments(mode)
        for experiment in experiments:
            if not hasattr(experiment, 'data_list'):
                experiment.load_data()
            for attr_name, attr_var in attributes.items():
                setattr(experiment, attr_name, attr_var.get())
            experiment.process_data()

    def process(self):

        exps = self.get_experiments('selection')
        for exp in exps:
            exp.load_data()
            exp.process_data()

    def check_grouping(self, var, var2):
        if (var.get() is True) and (var2.get() is True):
            self.show_grouped(['folder', 'cycle'])        
        elif var.get() is True:
            self.show_grouped(['folder'])
        elif var2.get() is True:
            self.show_grouped(['cycle'])
        else:
            self.refresh_tree('all')

    def inspect(self):
        inspect_experiment(self.get_experiments('selection')[0])

    def save(self, **kwargs):
        experiments = self.get_experiments('all')
        process_and_save(self.manager, experiments)
        
