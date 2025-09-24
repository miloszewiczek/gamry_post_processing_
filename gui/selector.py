import tkinter as tk
from tkinter import ttk
from gui.tree_controller import TreeController

class Selector(ttk.Frame):
    def __init__(self, parent, loader, manager, on_move = None):
        super().__init__(parent)

        self.config_frame = ttk.Frame(self)
        self.config_frame.grid(column = 0, row = 0)

        self.data_treeview_label = ttk.Label(self.config_frame, text = 'Available experiments')
        self.data_treeview_label.grid(column = 0, row = 0)
        self.data_treeview = ttk.Treeview(self.config_frame)
        self.data_treeview.grid(column=0, row=1)
        self.data_treeview_controller = TreeController(loader = loader, manager = manager, tree = self.data_treeview)

        self.button_frame = ttk.Frame(self.config_frame)
        self.move_to_data_button = tk.Button(self.button_frame, text = '>>', command = lambda: self.move(self.data_treeview, self.analysis_treeview))
        self.move_to_data_button.grid(column = 0, row = 0, pady = 5)
        self.move_to_analysis_button = tk.Button(self.button_frame, text = '<<', command = lambda: self.move(self.analysis_treeview, self.data_treeview))
        self.move_to_analysis_button.grid(column=0, row= 1, pady = 5)
        self.button_frame.grid(column = 1, row = 1, padx = 10)

        self.data_treeview_label = ttk.Label(self.config_frame, text = 'To analysis')
        self.data_treeview_label.grid(column = 2, row = 0)
        self.analysis_treeview = ttk.Treeview(self.config_frame)
        self.analysis_treeview.grid(column=2, row = 1)
        self.analysis_treeview_controller = TreeController(loader = loader, manager = manager, tree = self.analysis_treeview)

        self.on_move = on_move


    def move(self, from_:ttk.Treeview, to:ttk.Treeview):

        for item_id in from_.selection():
            print(item_id)
            
            text = from_.item(item_id, 'text')
            values = from_.item(item_id, 'values')
            to.insert('', 'end', iid = item_id,  text = text, values = values)
            from_.delete(item_id)

        if self.on_move:
            self.on_move(self.analysis_treeview_controller)

    def get_controllers(self):
        return (self.data_treeview_controller, self.analysis_treeview_controller)