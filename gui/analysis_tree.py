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
        self.columns = columns
        self.headers = headers
        self.sizes = sizes

        if isinstance(columns, dict):
            self.columns, self.headers = tuple(columns.keys()), tuple(columns.values())
        
        if self.headers is None:
            self.headers = [column_name.capitalize() for column_name in columns]
        

        if isinstance(columns, str):
            self.columns = (columns,)
        if isinstance(headers, str):
            self.headers = (headers,)

        #main tree
        self.tree = ttk.Treeview(self, columns = self.columns)
        self.tree.grid(row = 0, column = 0)
        self.tree.column('#0', width = 50)
        self.tree.heading('#0', text = 'Name')

        #changing column names to headings provided by the user
        for col, header, size in zip(self.columns, self.headers, sizes):
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
        


    def add_analysis(self, values:tuple, aux:dict = None, name:str = None, ask = False, image = None):
        
        #if ask is True, user gets to pick the analysis name
        if ask is True:
            name = askstring('Analysis', 'Give name of the analysis')
        
        #default 
        elif (ask is False) and (name is None): 
            name = str(self.counter) + 'A'
        #else, name is used

        #makign sure its a tuple
        print(type(values))
        if not isinstance(values, tuple):
            values = (values,)

        print(values)
        #creating a TreeNode
        tree_view_node = TreeNode(self.counter,
                                  name,
                                  'analysis',
                                  'None',
                                  values = {key: val for key, val in zip(self.headers, values)},
                                  other_info = aux,
                                  image = image)
        #assigning to a dict
        self.analyses[str(self.counter)] = tree_view_node

        #adding to treeview
        self.tree.insert('', 'end', iid = self.counter, text = name, values = values)
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
        node = self.analyses[self.tree.selection()[0]]
        x = tk.Toplevel(self)
        ntbk = ttk.Notebook(x)
        ntbk.pack(fill="both", expand=True)

        class info_tab(ttk.Frame):
            def __init__(self, parent, **kwargs):
                super().__init__(parent)
                for i, (item, value) in enumerate(kwargs.items()):
                    ttk.Label(self, text=item).grid(row=i, column=0, sticky="w")
                    ttk.Label(self, text=value).grid(row=i, column=1, sticky="w")

        #unpack node.main_info dict into kwargs
        page1 = info_tab(ntbk, **node.main_info)
        page1.pack(fill="both", expand=True)

        page2 = info_tab(ntbk, **node.other_info)
        page2.pack(fill = 'both', expand = True)

        ntbk.add(page1, text = 'Main Info')
        ntbk.add(page2, text = 'Other Info')