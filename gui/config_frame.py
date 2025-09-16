import tkinter as tk
from tkinter import ttk
from .functions import process, process_and_save, dump, load_settings
from unicode_mapping import uni_map
from .tree_controller import TreeController

class ConfigFrame(ttk.Labelframe):
    def __init__(self, parent, controller: TreeController):
        super().__init__(parent, text = 'Configuration')
        self.controller = controller
        

        #UNCOMPENSATED RESISTANCE
        self.Ru_label = tk.Label(self, text = f'Uncompensated resistance [{uni_map['Ohm']}]')
        self.Ru_var = tk.DoubleVar(value=0)
        self.Ru_cbox = ttk.Combobox(self, textvariable = self.Ru_var)
        self.apply_Ru_btn = tk.Button(self, 
                                      text = '+', 
                                      command = lambda: self.controller.apply_attr_to_selected(self.Ru_var, 'Ru'))


        #GEOMETRICAL AREA
        self.geometrical_area_label = tk.Label(self, text = f'Geometric Area [cm{uni_map['square']}]', justify='left')
        self.geometrical_area_var = tk.DoubleVar(value = 0.07069)
        self.geometrical_area_entry = ttk.Combobox(self, textvariable = self.geometrical_area_var)
        self.geometrical_area_entry['values'] = (0.07069, 
                                               0.007854, 
                                               0.196, 
                                               0.08)
        self.geometrical_area_btn = tk.Button(self, 
                                text = '+', 
                                command = lambda: self.controller.apply_attr_to_selected(self.geometrical_area_var, 'geometrical_area'))

        #REFERENCE POTENTIAL
        self.reference_potential_label = tk.Label(self, text = f'Reference Electrode potential [V]', justify = 'left')
        self.reference_potential_var = tk.DoubleVar(value = 0.21)
        self.reference_potential_entry = ttk.Combobox(self, textvariable= self.reference_potential_var)
        self.reference_potential_entry['values'] = ('0.21', '0.255')
        self.reference_potential_btn = tk.Button(self, 
                                text = '+', 
                                command = lambda: self.controller.apply_attr_to_selected(self.reference_potential_var, 'reference_potential'))  

        self.settings = {'Ru': self.Ru_var, 'geometrical_area' : self.geometrical_area_var, 'reference_potential': self.reference_potential_var}
        self.apply_all_btn = ttk.Button(self, text = 'Apply all', command = lambda: self.controller.apply_multiple(self.settings))
        self.apply_all_btn.grid(column = 3, row = 1, padx = 10, sticky = 'we')
        
        self.get_raport = ttk.Button(self, text = 'Save settings', command = lambda: dump(self.settings))
        self.get_raport.grid(column = 3, row = 2, padx = 10, sticky = 'we')

        self.load_settings = ttk.Button(self, text = 'Load settings', command = lambda: load_settings(self.settings))
        self.load_settings.grid(column = 3, row = 0, padx = 10, sticky = 'we')

        self.geometrical_area_label.grid(column= 0, row = 0, sticky = 'w', padx = 10)
        self.reference_potential_label.grid(column= 0, row = 1, sticky = 'w', padx = 10)
        self.Ru_label.grid(column = 0, row = 2, sticky = 'w', padx = 10)

        self.geometrical_area_entry.grid(column = 1, row = 0)
        self.reference_potential_entry.grid(column = 1, row = 1)
        self.Ru_cbox.grid(column = 1, row = 2)
        
        self.geometrical_area_btn.grid(column = 2, row = 0, sticky ='w', ipadx = 2, ipady= 2)
        self.reference_potential_btn.grid(column = 2, row = 1, ipadx = 2, ipady= 2)
        self.apply_Ru_btn.grid(column = 2, row = 2, ipadx = 2, ipady= 2)



