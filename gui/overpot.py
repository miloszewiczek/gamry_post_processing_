import tkinter as tk
from tkinter import ttk
from functions.functions import calc_closest_value
from gui.functions import variable_separation
import pandas as pd
from core import Experiment
from pandastable import Table, config


class OverpotWindow(tk.Toplevel):
    def __init__(self, parent, experiments: list[Experiment]):
        super().__init__(parent)
        self.experiments = experiments
        self.parent = parent
        self.gui()


    def on_ok(self):
        benchark_currents = variable_separation(self.current_densities_var.get(), ',', float)
        #divide to obtain A/cm2
        benchark_currents = [current/1000 for current in benchark_currents]
        columns = ['E_iR vs RHE [V]', 'J_GEO [A/cm2]']
        x = []
        for exp in self.experiments:

            #need to fix get_columns because curves parameter is now in it
            df = exp.get_columns(curve = 0, columns = columns)
            potentials = df.iloc[:,0]
            current = df.iloc[:,1]
            c = pd.DataFrame([calc_closest_value(benchark_currents, current, potentials, mode = 'first')], index = [exp.file_name], columns = benchark_currents)
            x.append(c)
        x = pd.concat(x)
        x_transf = x.T
        x_transf['mean'] = x_transf.mean(axis = 1)
        x_transf['std'] = x_transf.std(axis = 1)


        self.table_frame = tk.Frame(self)
        self.table_frame.grid(row = 1, column = 0)
        self.table = pt = Table(self.table_frame, dataframe = x_transf, showstatusbar = True, showtoolbar = True)
        self.table.grid(row = 3, column = 0)
        pt.show()

        #self.parent.analysis.add_analysis(x_transf, aux = {'Dopa': 'dopa'})
        
    def gui(self):
        
        #main frame
        self.main_frame = tk.Frame(self)
        self.main_frame.grid(row = 0, column = 0)

        self.current_densities_var = tk.StringVar(value = -10)
        self.overpots_entry = tk.Entry(self.main_frame, textvariable = self.current_densities_var)
        tk.Label(self.main_frame, text = 'Calculate the overpotentials at given current densities.\n' \
        'You can calculate the overpotentials at more than one current density,\n' \
        'by separating the valeus with a comma.', justify = 'left').grid(row = 0, column = 0, padx = 10, pady = 5)
        tk.Label(self.main_frame, text = 'Current densities [mA/cm2]', justify = 'left').grid(row = 1, column = 0, sticky = 'w', padx = 10)
        self.overpots_entry.grid(row = 1, column = 1, sticky = 'we')
        tk.Button(self.main_frame, text = 'Calculate', command = self.on_ok).grid(row = 2, column = 1)
        tk.Button(self.main_frame, text = 'Cancel', command = lambda: self.destroy()).grid(row = 2, column = 0)

        
        
