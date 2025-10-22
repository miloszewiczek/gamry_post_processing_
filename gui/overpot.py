import tkinter as tk
from tkinter import ttk
from functions.functions import calc_closest_value
from gui.functions import variable_separation
import pandas as pd

class OverpotWindow(tk.Toplevel):
    def __init__(self, parent, experiments):
        super().__init__(parent)
        self.experiments = experiments
        self.parent = parent
        self.gui()


    def on_ok(self):
        currents = variable_separation(self.current_densities_var.get(), ',', float)
        #divide to obtain A/cm2
        currents = [current/1000 for current in currents]
        columns = ['E_iR vs RHE [V]', 'J_GEO [A/cm2]']
        x = []
        for exp in self.experiments:

            #need to fix get_columns because curves parameter is now in it
            df = exp.get_columns(columns = columns)
            pot = df[columns[0]]
            cur = df[columns[1]]
            c = pd.DataFrame([calc_closest_value(currents, cur, pot, mode = 'first')], index = [exp.file_name], columns = currents)
            x.append(c)
        x = pd.concat(x)
        x_transf = x.T
        x_transf['mean'] = x_transf.mean(axis = 1)
        x_transf['std'] = x_transf.std(axis = 1)

        print(x)
        #self.parent.analysis.add_analysis(x_transf, aux = {'Dopa': 'dopa'})
        
    def gui(self):
        self.current_densities_var = tk.StringVar(value = -10)
        self.overpots_entry = tk.Entry(self, textvariable = self.current_densities_var)

        tk.Label(self, text = 'Current densities').grid(row = 0, column = 0)
        self.overpots_entry.grid(row = 0, column = 1)
        tk.Button(self, text = 'Calculate', command = self.on_ok).grid(row = 1, column = 1)
