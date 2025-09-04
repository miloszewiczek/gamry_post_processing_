import tkinter as tk
from tkinter import ttk
from .functions import inspect_wrapper, filter_experiments, copy_experiment, delete_selected, reset

class ExperimentTree(ttk.Frame):
    def __init__(self,parent):
        super().__init__(parent)
        self.manager = parent.manager
        self.loader = parent.loader

        #configuration
        self.columnconfigure(0, minsize = 300, weight =1)
        self.rowconfigure(2, minsize = 500, weight = 1)

        #create frame
        self.tree_frame = tk.Frame(self)
        self.tree_frame.grid(row=2, column = 0, sticky = 'nsew')
        
        #main tree
        self.filtered_tree = ttk.Treeview(self.tree_frame)
        self.filtered_tree.heading('#0', text ='Type')
        self.filtered_tree.column('#0', width = 50)   
        self.filtered_tree.pack(side='left', fill = tk.BOTH, expand = 1)
        vsb = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.filtered_tree.yview)
        vsb.pack(side='right', fill='both')
        self.filtered_tree.configure(yscrollcommand= vsb.set)
        self.filtered_tree.bind('<Double-Button-1>', lambda event: inspect_wrapper(event, self.filtered_tree, self.manager))
        
        #filtering actions
        self.filtering_actions_frame = tk.LabelFrame(self, text = 'Filtering tree actions', bd = 1, relief = 'groove')
        self.filtering_actions_frame.grid(row=0, column = 0, sticky = 'nsew', pady = 5)
        self.filtering_actions_frame.rowconfigure(0, weight = 0)
        self.filter_btn = tk.Button(self.filtering_actions_frame, text = 'Filter', command = lambda: filter_experiments(self.filtered_tree, self.manager, self.current_filter_var))
        self.filter_btn.grid(row = 0, column = 0, padx = 5, pady = 5, sticky = 'w')
        self.reset_filter_btn = tk.Button(self.filtering_actions_frame, text = 'Reset', command = lambda: reset(self.filtered_tree, self.manager))
        self.reset_filter_btn.grid(row=0, column = 1, pady = 5)

        #additional buttons
        tk.Button(self.filtering_actions_frame, text = 'Copy', command = lambda: copy_experiment(parent.loader,
                                                                                         self.filtered_tree,
                                                                                         self.manager)
                                                                                        ).grid(row=0,column=2, padx = 5, pady = 5)
        tk.Button(self.filtering_actions_frame, text = 'Delete', command = lambda: delete_selected(self.filtered_tree,
                                                                                           self.manager)
                                                                                        ).grid(row=0,column=3, padx = 5, pady=5, sticky = 'e')

        self.current_filter_frame = tk.Frame(self)
        self.current_filter_frame.grid(row=1, column =0)
        self.current_filter_var = tk.StringVar(value = 'No filter applied')
        self.current_filter_label = tk.Label(self.current_filter_frame, textvariable=self.current_filter_var)
        self.current_filter_label.grid(row=0, column = 0)

