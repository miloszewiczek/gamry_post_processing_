import tkinter as tk
from tkinter import ttk
from tkinter.simpledialog import askstring
from .treenode import TreeNode
from pandas import DataFrame
from .tree_controller import TreeController

class AnalysisTree(ttk.Frame):
    
    def __init__(self, parent, columns: tuple[str], headers:tuple[str] = None, sizes: tuple[int] = None):
        super().__init__(parent)
        self.analyses = {}
        self.counter = 0
        if headers is None:
            headers = [column_name.capitalize() for column_name in columns]

        if isinstance(columns, str):
            columns = (columns,)
        if isinstance(headers, str):
            headers = (headers,)

        #main tree
        self.tree = ttk.Treeview(self, columns = columns)
        self.tree.grid(row = 0, column = 0)
        self.tree.column('#0', width = 50)
        self.tree.heading('#0', text = 'Name')

        #changing column names to headings provided by the user
        for col, header, size in zip(columns, headers, sizes):
            self.tree.column(col, width = size)
            self.tree.heading(col, text = header)

        #auxiliary stuff
        self.options_frame = ttk.Frame(self)
        self.options_frame.grid(row = 0, column = 1, sticky = 'ns')
        self.delete_btn = ttk.Button(self.options_frame, command = self.delete_node, text = '-')
        self.delete_btn.grid(row = 0, column = 0)

        self.save_analyses_btn = ttk.Button(self.options_frame, command = self.save_treeview, text = 'Save')
        self.save_analyses_btn.grid(row = 1, column = 0)

        self.tree.bind('<Double-Button-1>', lambda x: self.inspect(x))
        


    def add_analysis(self, values:tuple, aux:dict = None):

        if values is str:
            values = (values,)
        
        analysis_name = askstring('Analysis', 'Give name of the analysis')
        tree_view_node = TreeNode(self.counter,
                                  analysis_name,
                                  'analysis',
                                  'None',
                                  values = values,
                                  other_info = aux)
        self.analyses[str(self.counter)] = tree_view_node

        self.tree.insert('', 'end', iid = self.counter, text = analysis_name, values = values)
        self.counter += 1
        return tree_view_node

    def save_treeview(self, tree: ttk.Treeview = None):

        if tree is None:
            tree = self.tree
            
        list_to_df = []
        for row_id in tree.get_children():
            row_item = tree.item(row_id, 'values')
            list_to_df.append(row_item)

        # Get column headings
        col_headings = [tree.heading(col)["text"] for col in tree["columns"]]    
        DataFrame(list_to_df, columns = col_headings).to_excel('test.xlsx', engine = 'openpyxl')


    def delete_node(self):
        self.tree.delete(self.tree.selection())

    def inspect(self, event):
        node = self.analyses[self.tree.selection()[0]].other_info
        x = tk.Toplevel(self)
        for i, (key, val) in enumerate(node.items()):

            tk.Label(x, text = key).grid(row = i, column = 0)
            if isinstance(val, list):
                tmp = tk.Listbox(x)
                tmp.grid(row = i, column = 1)
                for item in val:
                    tmp.insert(tk.END, item)
            else:
                tk.Label(x, text = val).grid(row = i, column = 1)