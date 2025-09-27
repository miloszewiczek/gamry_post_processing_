import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from gui import TreeNode
from gui.functions import delete_selected
import math
from tkinter.simpledialog import askstring
from experiments.base import Experiment
from .tree_controller import TreeController
from .functions import plot_experiment, clear_plot
import pandas as pd
import seaborn as sns
from .analysis_tree import AnalysisTree
from .selector import Selector


class InteractivePlotApp(tk.Toplevel):
    def __init__(self, parent, data, callback = None):
        super().__init__()

        self.parent = parent
        self.analyses: dict[str, TreeNode] = {}
        self.title('Double Layer Calculator')

        self.callback = callback

        self.plot_frame = ttk.Frame(self)
        self.plot_frame.grid(column = 0, row = 1, sticky = 'nsew')

        # Create figure
        self.fig, (self.ax1, self.ax2) = plt.subplots(nrows = 1, ncols = 2, gridspec_kw= {'width_ratios':[2, 1]})
        self.selector = Selector(self, parent.loader, parent.manager, on_move = self.update_plot)
        self.tree1_cont, self.tree2_cont = self.selector.get_controllers()
        self.selector.grid(column = 0, row = 0)

        self.ax1.set_xlabel(r"$E \ vs \ RHE\  [V]$")
        self.ax1.set_ylabel(r"$J_{GEO}\  [A/cm^2]$")
        self.ax1.set_title("Cyclic Voltammetry Scans")

        self.ax2.set_title(r"Charging currents - $C_{DL}$")
        self.ax2.set_xlabel(r"$Scanrate\  [mV/s]$")

        #need to change the units on this thing!
        self.ax2.set_ylabel(r"$\Delta \ J_{GEO}$ $[A/cm^2]$")

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.draw_idle()

        # Label for info
        #Slider
        self.input_frame = ttk.Frame(self)
        self.input_frame.grid(column = 0, row = 2)

        self.vline_pos = tk.DoubleVar(value = 0)
        self.slider = ttk.Scale(self.input_frame, from_ = -1, to = 1, orient = 'horizontal', command = self.on_slider_move, variable = self.vline_pos)
        self.slider.bind('<ButtonRelease-1>', self.on_slider_release)
        self.slider.grid(column = 0, row = 0, sticky = 'we')
        
        #entry (combined with slider)
        self.potential_entry = ttk.Entry(self.input_frame, textvariable = self.vline_pos)
        self.potential_entry.bind('<FocusOut>', self.on_focus_out)
        self.potential_entry.bind('<Return>', self.on_focus_out)
        self.potential_entry.grid(column = 0, row = 1, sticky = 'we')

        self.analysis_list = []
        self.add_analysis_btn = ttk.Button(self.input_frame, text = 'Add analysis', command = self.add_analysis)
        self.add_analysis_btn.grid(row = 3, column = 3)

        self.begin_analysis_btn = ttk.Button(self.input_frame, text = 'Begin analysis', command = self.set_lines)
        self.begin_analysis_btn.grid(row = 3, column = 1)


        self.col_headers = {'potential': 'Potential [V]', 'Cdl': 'CDL [F]', 'b': 'b [F/mV/s]'}
        self.saved_analyses = AnalysisTree(self, columns = self.col_headers,
                                           sizes = (200, 75, 75, 75))

        self.saved_analyses.grid(row=0, column = 3)
        self.analysis_counter = 1

        self.calculate_map_btn = ttk.Button(self, text = 'MAP ME, BITCH', command = lambda: self.calculate_map())
        self.calculate_map_btn.grid(column = 4, row = 0)

        self.initialize(tree = self.tree1_cont.tree, data = data)
        self.tree1_cont.tree.bind('<<TreeviewSelect>>', self.plot_previews)

    def initialize(self, tree, data: list[Experiment]):
        for experiment in data:
            tree.insert('', 'end', experiment.id, text = experiment.file_name)

    def add_analysis(self):

        CDL = f'{self.results[0]:.2e}'
        b = f'{self.results[1]:.2e}'
        potential = f'{self.vline_pos.get()}'
        experiments_from_analysis = self.tree2_cont.get_experiments('all')
        file_paths = [exp.file_path for exp in experiments_from_analysis]
        node = self.saved_analyses.add_analysis(values = (potential, CDL, b), aux = {'Filepath' : 'x', 'test': 'dooppa'}, ask = True)

        #adding the analysis to main window
        self.callback('dupa', node.__dict__, node.text)

        

    def on_focus_out(self, event):
        self.on_slider_move(event)
        self.on_slider_release(event)


    def on_slider_move(self, event):
        val = self.vline_pos.get()

        self.vline.set_xdata([val,val])
        self.canvas.draw_idle()


    def on_slider_release(self, *args):
        scanrates, current_differences = self.calculate_difference(self.vline_pos.get())
        self.plot_cdl(scanrates, current_differences)
        a, b = self.calculate_regression_line(scanrates, current_differences)
        self.plot_line(a, b, scanrates)
        
        self.results = (a, b)

    def calculate_difference(self, potential):

        #this also returns the vertical line, have to filter it out! (WIP)
        scanrates = []
        current_differences = []

        for i, line in enumerate(self.ax1.get_lines()):
            if line is self.vline:
                continue
            x_data = np.array(line.get_xdata())
            y_data = np.array(line.get_ydata())

            scanrate = line.experiment.meta_data['SCANRATE']
            #grab the first two indices, one for each sweep
            idx = np.argsort(np.abs(x_data - potential))[:2]
            two_currents = y_data[idx]
            difference = abs(two_currents[0] - two_currents[1])
            #print(f'difference: {difference}, scanrate: {scanrate}')
            if scanrate in scanrates:
                continue
            scanrates.append(scanrate)
            current_differences.append(difference)

        return scanrates, current_differences

    def manual_update(self):
        self.on_slider_move()
        self.on_slider_release()

    def calculate_map(self):
        
        result = []
        
        min_x = self.slider.cget('from')
        max_x = self.slider.cget('to')
        y = np.arange(min_x, max_x, 0.001)
        y = np.round(y, 3)

        for potential in y:
            scanrates, current_differences = self.calculate_difference(potential = potential)
            result.append(current_differences)
        df = pd.DataFrame(result, columns = scanrates, index = y)
        plt.figure(figsize = (8,6))
        plt.imshow(df, cmap = 'viridis', interpolation = 'bicubic', origin = 'lower', aspect = 'auto')
        plt.colorbar()
        plt.title("2D Heatmap")
        plt.show()


    def plot_cdl(self, x: list, y: list):
        if not hasattr(self, "scatter_plot"):
            self.scatter_plot = self.ax2.scatter(x, y)
        else:
            self.scatter_plot.set_offsets(np.c_[x, y])

    def plot_line(self, a, b, x):
        x_array = np.array(x)
        y_array = a * x_array + b

        if not hasattr(self, 'regression_line'):
            # Create the line ONCE, store the Line2D object
            (self.regression_line,) = self.ax2.plot(x_array, y_array, color="red")
        else:
            # Update existing line
            self.regression_line.set_xdata(x_array)
            self.regression_line.set_ydata(y_array)
        
        self.ax2.relim()
        self.ax2.autoscale_view()
        self.canvas.draw_idle()
        
        
    def calculate_regression_line(self, x: list, y: list) -> tuple:
        
        slope, free_coefficient = np.polyfit(x, y, deg = 1)
        return slope, free_coefficient


    def get_data(self, controller:TreeController, selection_mode):
     
        return controller.get_nodes(selection_mode)

    def set_lines(self):
        
        experiments = self.tree2_cont.get_experiments('all')
        vline_min, vline_max = self.get_minmax_x(experiments)
        vline_position = vline_min + (vline_max - vline_min)/2
        self.slider.config(from_ = vline_min, to = vline_max)


        if not hasattr(self, 'vline'):
            self.vline = self.ax1.axvline(x=vline_position, color='red', linestyle='--', label="Slider Position")
        self.vline.set_xdata([vline_position, vline_position])
        self.canvas.draw_idle()

        return 
    
    def plot_data(self):
        
        clear_plot(self.ax1)
        experiments = self.tree2_cont.get_experiments('all')
        for experiment in experiments:
            plot_experiment(experiment, self.ax1, self.canvas, x_column = 'E vs RHE [V]', y_column = 'J_GEO [A/cm2]', alpha = 0.2)
    
    def plot_previews(self, event):
        # Make sure we have a list to track preview lines
        if not hasattr(self, "preview_lines"):
            self.preview_lines = []

        # Remove old preview lines
        for line in self.preview_lines:
            if line in self.ax1.lines:
                line.remove()
        self.preview_lines.clear()

        preview_datasets = self.tree1_cont.get_experiments('selection')
        # Plot new previews
        for preview_dataset in preview_datasets:
            lines = plot_experiment(preview_dataset, self.ax1, self.canvas, x_column = 'E vs RHE [V]', y_column= 'J_GEO [A/cm2]', alpha = 0.2)
            self.preview_lines.extend(lines)
            
        self.canvas.draw_idle()

    def get_minmax_x(self, experiments:list[Experiment]):
        
        #ensure that first minimum is always bigger
        min_val = math.inf
        #or maximum - smaller
        max_val = -math.inf

        for experiment in experiments:
            result = experiment.get_columns(columns = ['E vs RHE [V]'])
            min_val = min(min_val, np.min(result))
            max_val = max(max_val, np.max(result))
            self.x = result

        return min_val, max_val
    
    def get_resolution(self, experiments: list[Experiment]):
        #Helper function for getting data

        return min({experiment.get_parameter('STEPSIZE') for experiment in experiments})

    def update_plot(self, event):
        self.ax1.clear()
        experiments = self.tree2_cont.get_experiments('all')
        for experiment in experiments:
            plot_experiment(experiment, self.ax1, self.canvas, x_column = 'E vs RHE [V]', y_column = 'J_GEO [A/cm2]')

    def save_treeview(self, tree: ttk.Treeview):
        list_to_df = []
        for row_id in tree.get_children():
            row_item = tree.item(row_id, 'values')
            list_to_df.append(row_item)

        # Get column headings
        col_headings = [tree.heading(col)["text"] for col in tree["columns"]]    
        pd.DataFrame(list_to_df, columns = col_headings).to_excel('test.xlsx', engine = 'openpyxl')

if __name__ == "__main__":
    app = InteractivePlotApp()
    app.mainloop()