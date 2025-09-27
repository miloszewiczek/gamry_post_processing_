import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from functions.functions import calculate_slopes, interactive_selection
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

    def __init__(self, parent, data, callback):
        super().__init__()
        self.title("Tafel analysis")
        self.parent = parent
        self.xy_data = []
        self.callback = callback

        self.data_treeview = ttk.Treeview(self)
        self.data_treeview.grid(column = 0, row = 0)
        self.data_treeview_controller = TreeController(parent.loader, self.data_treeview, parent.manager)
        self.initialize(data)

        self.plot_frame = ttk.Frame(self)
        self.plot_frame.grid(column = 0, row = 1, columnspan = 3, sticky = 'we')

        # Create figure
        self.fig, self.ax = plt.subplots()

        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")
        
        self.canvas = FigureCanvasTkAgg(self.fig, master = self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.draw()
        toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        toolbar.update()

        
        self.config_frame = ttk.LabelFrame(self, text = 'Tafel calculation modes', relief = 'raised', borderwidth = 1)
        self.config_frame.grid(column = 1, row = 0)
        self.tafel_mode_var = tk.BooleanVar(value = True)
        ttk.Radiobutton(self.config_frame,
                        text = 'Normal',
                        variable = self.tafel_mode_var,
                        value = True,
                        command = lambda: toggle_widgets(self.tafel_mode_var, [self.slider_start, self.overlap_slider, self.interval_slider])
        ).grid(column = 0, row = 0)

        ttk.Radiobutton(self.config_frame,
                        text = 'Interval-based',
                        variable = self.tafel_mode_var,
                        value = False,
                        command = lambda: toggle_widgets(self.tafel_mode_var, [self.slider_start, self.overlap_slider, self.interval_slider])
        ).grid(column = 1, row = 0)


        tk.Label(self.config_frame, text = 'Starting potential [V]').grid(column = 0, row = 1, columnspan = 2)
        self.start_var = tk.DoubleVar(value = -0.025)
        self.slider_start = tk.Scale(self.config_frame, variable= self.start_var, orient = 'horizontal', from_ = -1, to =0, resolution = 0.0001)
        self.slider_start.bind('<ButtonRelease-1>', self.on_slider_release)
        self.slider_start.grid(column = 0, row = 2)
        self.start_entry = tk.Entry(self.config_frame, textvariable=self.start_var)
        self.start_entry.grid(column = 1, row = 2)

        tk.Label(self.config_frame, text = 'Interval [V]').grid(column = 0, row = 3, columnspan = 2)
        self.interval_var = tk.DoubleVar(value = -0.005)
        self.interval_slider = tk.Scale(self.config_frame, variable= self.interval_var, from_ = -0.05, to = 0.05, resolution = 0.001, orient = 'horizontal')
        self.interval_slider.bind('<ButtonRelease-1>', self.on_slider_release)
        self.interval_slider.grid(column = 0, row = 4)
        self.interval_entry = tk.Entry(self.config_frame, textvariable=self.interval_var)
        self.interval_entry.grid(column = 1, row = 4)

        tk.Label(self.config_frame, text = 'Overlap [V]').grid(column = 0, row = 5, columnspan = 2)
        self.overlap_var = tk.DoubleVar(value = -0.0025)
        self.overlap_slider = tk.Scale(self.config_frame, variable= self.overlap_var, orient = 'horizontal', from_ = -0.05, to = 0.05, resolution = 0.001)
        self.overlap_slider.bind('<ButtonRelease-1>', self.on_slider_release)
        self.overlap_slider.grid(column = 0, row = 6, padx = 5)
        self.overlap_entry = tk.Entry(self.config_frame, textvariable=self.overlap_var)
        self.overlap_entry.grid(column = 1, row = 6, padx = 5)

        tk.Button(self.config_frame, command = self.generate_tafel_plot, text = 'Generate').grid(column = 0, row = 7, padx = 5, pady = 5)

        self.analysis_tree = AnalysisTree(self, ('slope',), ('Tafel slope [V/dec]',), (150,))
        self.analysis_tree.grid(column = 3, row = 0)

        tk.Button(self.config_frame, text = 'Select', command = self.interactive_mode).grid(column = 1, row = 7, padx = 5, pady = 5)


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
                x, y = calculate_slopes(tafel_curve, start_pot, interval, overlap, normal_mode = self.tafel_mode_var.get())
                self.ax.scatter(x, y)
                self.current_name = exp.file_name
                self.canvas.draw_idle()
                

    def interactive_mode(self):
        
        #callback after user clicks twice
        def store_result(res):
            self.selection_result = res
            d = self.analysis_tree.add_analysis(values = (res), ask = True, aux = {'Doopa': 'dopa'})
            self.callback(d.other_info, d.__dict__, d.text)

        scatter_data = self.ax.collections[0].get_offsets()
        x, y = scatter_data[:, 0], scatter_data[:, 1]

        interactive_selection(self.ax, self.canvas, x, y, normal_mode = self.tafel_mode_var.get(), callback = store_result)
    
    def on_slider_release(self, event):
        self.generate_tafel_plot()