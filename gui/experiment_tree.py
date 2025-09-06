import tkinter as tk
from tkinter import ttk
from .functions import inspect_wrapper, filter_experiments, copy_experiment, delete_selected, reset, plot_selected, process

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
        self.tree = ttk.Treeview(self.tree_frame)
        self.tree.heading('#0', text ='Type')
        self.tree.column('#0', width = 50)   
        self.tree.pack(side='left', fill = tk.BOTH, expand = 1)
        vsb = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        vsb.pack(side='right', fill='both')
        self.tree.configure(yscrollcommand= vsb.set)
        self.tree.bind('<Double-Button-1>', lambda event: inspect_wrapper(event, self.tree, self.manager))

            #tag configuration
        self.tree.tag_configure('processed', background = 'lightgreen')

    
        #filtering actions
        self.filtering_actions_frame = tk.LabelFrame(self, text = 'Filtering tree actions', bd = 1, relief = 'groove')
        self.filtering_actions_frame.grid(row=0, column = 0, sticky = 'nsew', pady = 5)
        self.filtering_actions_frame.rowconfigure(0, weight = 0)
        
        #buttons
        self.filter_btn = tk.Button(self.filtering_actions_frame, text = 'Filter', command = lambda: filter_experiments(self.tree, self.manager, self.current_filter_var))
        self.reset_filter_btn = tk.Button(self.filtering_actions_frame, text = 'Reset', command = lambda: reset(self.tree, self.manager))

        self.copy_btn = tk.Button(self.filtering_actions_frame, text = 'Copy', command = lambda: copy_experiment(parent.loader,
                                                                                         self.tree,
                                                                                         self.manager)
                                                                                        )

        self.delete_btn = tk.Button(self.filtering_actions_frame, text = 'Delete', command = lambda: delete_selected(self.tree,
                                                                                           self.manager))

        self.process_btn = tk.Button(self.filtering_actions_frame, text = 'Process selected', command = lambda: process(self.tree, self.manager, 'selected'))
        self.process_all_btn = tk.Button(self.filtering_actions_frame, text = 'Process All', command = lambda: process(self.tree, self.manager, 'all'))

        
        self.buttons = [self.filter_btn, self.reset_filter_btn, self.copy_btn, self.delete_btn, self.process_btn, self.process_all_btn]
        for bttn in self.buttons:
            bttn.pack(side = 'left', padx = 2, pady = 5, ipadx = 2)

        self.current_filter_frame = tk.Frame(self)
        self.current_filter_frame.grid(row=1, column =0)
        self.current_filter_var = tk.StringVar(value = 'No filter applied')
        self.current_filter_label = tk.Label(self.current_filter_frame, textvariable=self.current_filter_var)
        self.current_filter_label.grid(row=0, column = 0)

