import tkinter as tk
from tkinter import ttk
from .functions import process, apply_attr_to_selected

class ConfigFrame(ttk.Labelframe):
    def __init__(self, parent):
        super().__init__(parent, text = 'Configuration')
        self.loader = parent.loader
        self.manager = parent.manager
        self.tree = parent.filtered_tree


        #UNCOMPENSATED RESISTANCE
        self.Ru_label = tk.Label(self,text = 'Uncompensated resistance [Ohm]')
        self.Ru_var = tk.DoubleVar(value=0)
        self.Ru_cbox = ttk.Combobox(self, textvariable = self.Ru_var)
        self.apply_Ru_btn = tk.Button(self, 
                                      text = '+', 
                                      command = lambda: apply_attr_to_selected(self.tree, self.manager, self.Ru_var, 'Ru'))


        #GEOMETRICAL AREA
        self.geometrical_area_label = tk.Label(self, text = 'Geometric Area [cm2]', justify='left')
        self.geometrical_area_var = tk.DoubleVar(value = 0.07069)
        self.geometrical_area_entry = ttk.Combobox(self, textvariable = self.geometrical_area_var)
        self.geometrical_area_entry['values'] = (0.07069, 
                                               0.007854, 
                                               0.196, 
                                               0.08)
        self.geometrical_area_btn = tk.Button(self, 
                                text = '+', 
                                command = lambda: apply_attr_to_selected(self.tree, self.manager, self.geometrical_area_var, 'geometrical_area'))

        #REFERENCE POTENTIAL
        self.reference_potential_label = tk.Label(self, text = 'Reference Electrode potential [V]', justify = 'left')
        self.reference_potential_var = tk.DoubleVar(value = 0.21)
        self.reference_potential_entry = ttk.Combobox(self, textvariable= self.reference_potential_var)
        self.reference_potential_entry['values'] = ('0.21', '0.255')
        self.reference_potential_btn = tk.Button(self, 
                                text = '+', 
                                command = lambda: apply_attr_to_selected(self.tree, self.manager, self.reference_potential_var, 'reference_potential'))        
        
        #PROCESSING BUTTONS
        self.process_btn = tk.Button(self, text = 'Process selected', command = lambda: process(self.tree, self.manager, 'selected'))
        self.process_all_btn = tk.Button(self, text = 'Process All', command = lambda: process(self.tree, self.manager, 'all'))
        

        self.geometrical_area_label.grid(column= 0, row = 0, sticky = 'w')
        self.reference_potential_label.grid(column= 0, row = 1, sticky = 'w')
        self.Ru_label.grid(column = 0, row = 2, sticky = 'w')

        self.geometrical_area_entry.grid(column = 1, row = 0)
        self.reference_potential_entry.grid(column = 1, row = 1)
        self.Ru_cbox.grid(column = 1, row = 2)
        
        self.geometrical_area_btn.grid(column = 2, row = 0, sticky ='w')
        self.reference_potential_btn.grid(column = 2, row = 1 )
        self.apply_Ru_btn.grid(column = 2, row = 2)

        self.process_btn.grid(column = 3, row=1, sticky = 'e')
        self.process_all_btn.grid(column = 3, row=2, sticky = 'e')