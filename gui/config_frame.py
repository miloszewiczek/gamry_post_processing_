import tkinter as tk
from tkinter import ttk
from .functions import process, apply_attr_to_all

class ConfigFrame(ttk.Labelframe):
    def __init__(self, parent):
        super().__init__(parent, text = 'Configuration')
        self.loader = parent.loader
        self.manager = parent.manager
        self.tree = parent.filtered_tree


            #UNCOMPENSATED RESISTANCE
        tk.Label(self,text = 'Uncompensated resistance [Ohm]').grid(column=0, row =0, sticky = 'w')
        self.Ru_var = tk.StringVar(value=0)
        self.Ru_cbox = ttk.Combobox(self, textvariable = self.Ru_var)
        self.Ru_cbox.grid(column = 1, row =0)

            #GEOMETRIC AREA
        tk.Label(self, text = 'Geometric Area [cm2]', justify='left').grid(column=0, row = 1, sticky = 'w')
        self.geometrical_area_var = tk.StringVar(value = '0.07069')
        self.geometrical_area_entry = ttk.Combobox(self, textvariable = self.geometrical_area_var)
        self.geometrical_area_entry['values'] = ('0.07069)', 
                                               '0.007854', 
                                               '0.196', 
                                               '0.08')
        self.geometrical_area_entry.grid(column=1, row =1)
        self.apply_Ru_btn = tk.Button(self, 
                                      text = 'Apply to all', 
                                      command = apply_attr_to_all)
        self.apply_Ru_btn.grid(column=0, row =3)

            #REFERENCE POTENTIAL
        tk.Label(self, text = 'Reference Electrode potential [V]', justify = 'left').grid(column=0, row = 2, sticky = 'w')
        self.reference_electrode_var = tk.DoubleVar(value = 0.21)
        self.reference_electrode_entry = ttk.Combobox(self, textvariable= self.reference_electrode_var)
        self.reference_electrode_entry['values'] = ('0.21', '0.255')
        self.reference_electrode_entry.grid(column=1, row = 2)


        self.process_btn = tk.Button(self, text = 'Process selected', command = lambda: process(self.tree, self.manager, 'selected'))
        self.process_btn.grid(row=3, column = 1)

        self.process_all_btn = tk.Button(self, text = 'Process All', command = lambda: process(self.tree, self.manager, 'all'))
        self.process_all_btn.grid(row=3, column =2 )