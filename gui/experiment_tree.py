import tkinter as tk
from tkinter import ttk
from .tree_controller import TreeController

class ExperimentTree(ttk.Frame):
    def __init__(self,parent, manager, loader):
        super().__init__(parent)
        self.manager = manager
        self.loader = loader
        self.groupvar = tk.BooleanVar(value = False)
        self.groupvar2 = tk.BooleanVar(value = False)
        
        #create frame
        self.tree_frame = tk.Frame(self)
        self.tree_frame.grid(row=2, column = 0, sticky = 'nsew')
        self.tree = ttk.Treeview(self.tree_frame)
        print('My tree is: ',self.tree)
        self.controller = TreeController(self.loader, self.tree, self.manager)
        print('The controller tree is: ', self.controller.tree)

        #configuration
        self.columnconfigure(0, minsize = 300, weight =1)
        self.rowconfigure(2, minsize = 500, weight = 1)

        
        self.tree.heading('#0', text ='Type')
        self.tree.column('#0', width = 50)   
        self.tree.pack(side='left', fill = tk.BOTH, expand = 1)
        vsb = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        vsb.pack(side='right', fill='both')
        self.tree.configure(yscrollcommand= vsb.set)
        self.tree.bind('<Double-Button-1>', lambda event: self.controller.inspect())

            #tag configuration
        self.tree.tag_configure('processed', background = 'lightgreen')

        #filtering actions
        self.filtering_actions_frame = tk.LabelFrame(self, text = 'Filtering tree actions', bd = 1, relief = 'groove')
        self.filtering_actions_frame.grid(row=0, column = 0, sticky = 'nsew', pady = 5)
        self.filtering_actions_frame.rowconfigure(0, weight = 0)
        
        #buttons
        self.filtering_btn = ttk.Button(self.filtering_actions_frame, text = 'Filter', command = self.controller.filter)
        self.select_all_btn = ttk.Button(self.filtering_actions_frame, text = 'Select all', command = self.controller.select_or_deselect_all)
        self.process_all_btn = ttk.Button(self.filtering_actions_frame, text = 'Process', command = self.controller.process)
        self.copy_btn = tk.Button(self.filtering_actions_frame, text = 'Copy', command = self.controller.copy_nodes)
        self.delete_btn = tk.Button(self.filtering_actions_frame, text = 'Delete', command = self.controller.delete_nodes)
        self.save_btn = tk.Button(self.filtering_actions_frame, text = 'Save selected', command = self.controller.save)

        btns = [self.filtering_btn, self.select_all_btn, self.process_all_btn, self.copy_btn, self.delete_btn, self.save_btn]
        for btn in btns:
            btn.pack(side = 'left', padx = 2, pady = 2)

        self.grouping_checkbox = ttk.Checkbutton(self.filtering_actions_frame,
                                                text = 'Group by cycle',
                                                onvalue = True,
                                                offvalue = False,
                                                variable = self.groupvar,
                                                command = lambda: self.controller.check_grouping(self.groupvar, self.groupvar2))
        self.grouping_checkbox.pack()

        self.grouping_checkbox2 = ttk.Checkbutton(self.filtering_actions_frame,
                                                text = 'Group by Folder',
                                                onvalue = True,
                                                offvalue = False,
                                                variable = self.groupvar2,
                                                command = lambda: self.controller.check_grouping(self.groupvar, self.groupvar2))
        self.grouping_checkbox2.pack()

    def get_controller(self):
        return self.controller