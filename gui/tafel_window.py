import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from functions.functions import calculate_slopes

class tafel_window(tk.Toplevel):

    def __init__(self, parent):
        super().__init__()
        self.title("Interactive Vertical Line Plot")
        self.geometry("1000x1000")
        self.parent = parent
        self.xy_data = []


        self.config_frame = ttk.Frame(self)
        self.config_frame.pack()

        self.data_treeview = ttk.Treeview(self.config_frame)
        self.data_treeview.grid(column=0, row=0)

        self.test = ttk.Button(self.config_frame, text = 'TESTING', command = self.get_data)
        self.test.grid(column=1,row=3)

        self.plot_frame = ttk.Frame(self)
        self.plot_frame.pack()

        # Create figure
        self.fig, self.ax = plt.subplots()

        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.draw()


        tk.Label(self.config_frame, text = 'Starting potential [V]').grid(column=0, row = 2)
        self.start_var = tk.DoubleVar(value = -0.025)
        self.slider_start = tk.Scale(self.config_frame, variable= self.start_var, orient = 'horizontal', from_ = -1, to =0, resolution = 0.0001)
        self.slider_start.grid(column=1, row = 2)
        self.start_entry = tk.Entry(self.config_frame, textvariable=self.start_var)
        self.start_entry.grid(column = 2, row = 2)

        tk.Label(self.config_frame, text = 'Interval [V]').grid(column=0, row = 3)
        self.interval_var = tk.DoubleVar(value = -0.005)
        self.interval_slider = tk.Scale(self.config_frame, variable= self.interval_var, from_ = -1, to = 1, resolution = 0.0001, orient = 'horizontal')
        self.interval_slider.grid(column=1,row=3)
        self.interval_entry = tk.Entry(self.config_frame, textvariable=self.interval_var)
        self.interval_entry.grid(column = 2, row = 3)

        tk.Label(self.config_frame, text = 'Overlap [V]').grid(column=0, row = 4)
        self.overlap_var = tk.DoubleVar(value = -0.0025)
        self.overlap_slider = tk.Scale(self.config_frame, variable= self.overlap_var, orient = 'horizontal', from_ = -1, to = 1, resolution = 0.0001)
        self.overlap_slider.grid(column=1, row = 4)
        self.overlap_entry = tk.Entry(self.config_frame, textvariable=self.overlap_var)
        self.overlap_entry.grid(column = 2, row = 4)
        


        tk.Button(self.config_frame, text = 'print data', command = self.print_data).grid(row=5, column =0)
    def get_data(self):

        experiment_mappings = get_experiments(self.data_treeview, self.parent.manager, mode = 'selected')
        return experiment_mappings
    
    def print_data(self):

        start_pot = float(self.start_var.get())
        overlap = float(self.overlap_var.get())
        interval = float(self.interval_var.get())

        experiments = get_experiments(self.data_treeview, self.parent.manager, mode = 'selected')
        for exp in experiments:
            for tafel_curve in getattr(exp, 'tafel_curves'):
                calculate_slopes(tafel_curve, start_pot, interval, overlap)
                

