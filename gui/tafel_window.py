import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from functions.functions import calculate_slopes
from experiments.base import Experiment
from .tree_controller import TreeController
from .analysis_tree import AnalysisTree


def toggle_widgets(var: tk.BooleanVar, widgets: list[tk.Widget]):
    if var.get():
        for w in widgets:
            w.configure(state="disabled")
    else:
        for w in widgets:
            w.configure(state="normal")

class tafel_window(tk.Toplevel):

    def __init__(self, parent, data):
        super().__init__()
        self.title("Interactive Vertical Line Plot")
        self.parent = parent
        self.xy_data = []



        self.data_treeview = ttk.Treeview(self)
        self.data_treeview.grid(column = 0, row = 0)
        self.data_treeview_controller = TreeController(parent.loader, self.data_treeview, parent.manager)
        self.initialize(data)

        self.plot_frame = ttk.Frame(self)
        self.plot_frame.grid(column = 0, row = 1, columnspan = 2)

        # Create figure
        self.fig, self.ax = plt.subplots()

        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.draw()
        toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        toolbar.update()

        
        self.config_frame = ttk.Frame(self)
        self.config_frame.grid(column = 1, row = 0)
        self.tafel_mode_var = tk.BooleanVar(value = True)
        ttk.Label(self.config_frame, text = 'Tafel calculation modes').grid(column = 0, row = 0, columnspan = 2)
        ttk.Radiobutton(self.config_frame,
                        text = 'Normal',
                        variable = self.tafel_mode_var,
                        value = True,
                        command = lambda: toggle_widgets(self.tafel_mode_var, [self.slider_start, self.overlap_slider, self.interval_slider])
        ).grid(column = 0, row = 1)

        ttk.Radiobutton(self.config_frame,
                        text = 'Interval-based',
                        variable = self.tafel_mode_var,
                        value = False,
                        command = lambda: toggle_widgets(self.tafel_mode_var, [self.slider_start, self.overlap_slider, self.interval_slider])
        ).grid(column = 1, row = 1)


        tk.Label(self.config_frame, text = 'Starting potential [V]').grid(column = 1, row = 2, columnspan = 2)
        self.start_var = tk.DoubleVar(value = -0.025)
        self.slider_start = tk.Scale(self.config_frame, variable= self.start_var, orient = 'horizontal', from_ = -1, to =0, resolution = 0.0001)
        self.slider_start.grid(column = 1, row = 3)
        self.start_entry = tk.Entry(self.config_frame, textvariable=self.start_var)
        self.start_entry.grid(column = 2, row = 3)

        tk.Label(self.config_frame, text = 'Interval [V]').grid(column = 1, row = 4, columnspan = 2)
        self.interval_var = tk.DoubleVar(value = -0.005)
        self.interval_slider = tk.Scale(self.config_frame, variable= self.interval_var, from_ = -1, to = 1, resolution = 0.0001, orient = 'horizontal')
        self.interval_slider.grid(column = 1, row = 5)
        self.interval_entry = tk.Entry(self.config_frame, textvariable=self.interval_var)
        self.interval_entry.grid(column = 2, row = 5)

        tk.Label(self.config_frame, text = 'Overlap [V]').grid(column = 1, row = 6, columnspan = 2)
        self.overlap_var = tk.DoubleVar(value = -0.0025)
        self.overlap_slider = tk.Scale(self.config_frame, variable= self.overlap_var, orient = 'horizontal', from_ = -1, to = 1, resolution = 0.0001)
        self.overlap_slider.grid(column = 1, row = 7)
        self.overlap_entry = tk.Entry(self.config_frame, textvariable=self.overlap_var)
        self.overlap_entry.grid(column = 2, row = 7)

        tk.Button(self.config_frame, command = self.generate_tafel_plot, text = 'Generate').grid(column = 3, row = 8)

        self.analysis_tree = AnalysisTree(self, ('slope'), ('Tafel slope [V/dec]'))
        self.analysis_tree.grid(column = 3, row = 0)
        tk.Button(self, text = 'Save', command = self.analysis_tree.save_treeview).grid(column = 4, row = 1)


    def initialize(self, data: list[Experiment]):
        for experiment in data:
            self.data_treeview.insert('', 'end', experiment.id, text = experiment.file_name)
    
    def generate_tafel_plot(self):
        self.ax.clear()

        start_pot = float(self.start_var.get())
        overlap = float(self.overlap_var.get())
        interval = float(self.interval_var.get())

        experiments = self.data_treeview_controller.get_experiments('selection')
        for exp in experiments:
            for tafel_curve in getattr(exp, 'tafel_curves'):
                result = calculate_slopes(tafel_curve, start_pot, interval, overlap, 'sample', self.fig, self.ax, self.canvas, normal_mode = self.tafel_mode_var.get())
                self.canvas.draw_idle()
                self.result = result

