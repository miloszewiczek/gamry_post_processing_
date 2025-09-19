from tkinter import ttk
from tkinter.simpledialog import askstring
from .treenode import TreeNode
from pandas import DataFrame

class AnalysisTree(ttk.Treeview):
    
    def __init__(self, parent, columns: tuple[str], headers:tuple[str] = None):
        self.analyses = {}
        self.counter = 0
        if headers is None:
            headers = [column_name.capitalize() for column_name in columns]

        if isinstance(columns, str):
            columns = (columns,)
        if isinstance(headers, str):
            headers = (headers,)

        super().__init__(parent, columns = columns, show = 'headings')
        for col, header in zip(columns, headers):
            self.heading(col, text = header)

    def add_analysis(self, values:tuple):

        if values is str:
            values = (values,)
        
        analysis_name = askstring('Analysis', 'Give name of the analysis')
        tree_view_node = TreeNode(self.counter,
                                  analysis_name,
                                  'analysis',
                                  'None',
                                  other_info = values)
        self.analyses[self.counter] = tree_view_node

        self.insert('', 'end', iid = self.counter, text = self.counter, values = values)
        self.counter += 1

    def save_treeview(self, tree: ttk.Treeview = None):

        if tree is None:
            tree = self
            
        list_to_df = []
        for row_id in tree.get_children():
            row_item = tree.item(row_id, 'values')
            list_to_df.append(row_item)

        # Get column headings
        col_headings = [tree.heading(col)["text"] for col in tree["columns"]]    
        DataFrame(list_to_df, columns = col_headings).to_excel('test.xlsx', engine = 'openpyxl')
