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
from functions.functions import calculate_ECSA_from_slope

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
        self.ax1.set_ylabel(r"$I\  [A]$")
        self.ax1.set_title("Cyclic Voltammetry Scans")

        self.ax2.set_title(r"Charging currents - $C_{DL}$")
        self.ax2.set_xlabel(r"$Scanrate\  [mV/s]$")

        #need to change the units on this thing!
        self.ax2.set_ylabel(r"$\Delta \ I$ $[A]$")

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.draw_idle()
        self.canvas.get_tk_widget().bind('<Control-c>', self.get_dataframe_from_plot)

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
        self.potential_entry.grid(column = 0, row = 1, sticky = 'we', padx = 5, pady = 5)

        self.analysis_list = []
        self.add_analysis_btn = ttk.Button(self.input_frame, text = 'Add analysis', command = self.add_analysis)
        self.add_analysis_btn.grid(row = 1, column = 3, padx = 5, pady = 5)

        self.begin_analysis_btn = ttk.Button(self.input_frame, text = 'Begin analysis', command = self.set_lines)
        self.begin_analysis_btn.grid(row = 0, column = 3, padx = 5, pady = 5)

        self.copy_dataframe = ttk.Button(self.input_frame, text = 'Copy CDL plot', command = self.get_dataframe_from_plot)
        self.copy_dataframe.grid(row = 0, column = 4, padx = 5, pady = 5)

        self.col_headers = {'potential': 'Potential [V]',
                            'Cdl': 'CDL [F]', 'b': 'b [F/V/s]',
                            'Cdl_int': 'CDL integrate [F]', 'b_int': 'b integrate [F/V/s]',
                            'r^2': 'r^2 [-]',
                            'r^2_int': 'r^2 integrate [-]'}
        self.saved_analyses = AnalysisTree(self, columns = self.col_headers,
                                           sizes = (90, 90, 90, 90, 150, 50, 50))

        self.saved_analyses.grid(row = 0, column = 3)
        self.analysis_counter = 1

        self.curve_selection_var = tk.StringVar(self.input_frame, value = -1)
        self.curve_selector = ttk.Combobox(self.input_frame, values = (0, 1, 2, 'all', 'custom (WIP)'), textvariable = self.curve_selection_var)
        ttk.Label(self.input_frame, text = 'Curve').grid(row = 0, column = 1)
        self.curve_selector.grid(row = 1, column = 1, padx = 5, pady = 5)
        self.curve_selector.bind('<<ComboboxSelected>>', self.update_plot)


        self.calculate_map_btn = ttk.Button(self.input_frame, text = 'Create map', command = self.calculate_map)
        self.calculate_map_btn.grid(column = 4, row = 1, padx = 5, pady = 5)

        self.tree1_cont.initialize_tree(data = data)
        self.tree1_cont.tree.bind('<<TreeviewSelect>>', self.plot_previews)


    def add_analysis(self):

        CDL1, b1, r1 = self.results[0] #results is (line_calculations, integral calculations, dataframe)
        CDL2, b2, r2 = self.results[1] #in line and integral calculations: (slope, intercept, r_coefficient)
        r1_sqrt = r1**2 #making rcoefficient squared
        r2_sqrt = r2**2
        potential = f'{self.vline_pos.get()}' #potential at which the CDL was calculated
        node = self.saved_analyses.add_analysis(values = (potential, CDL1, b1, CDL2, b2, round(r1_sqrt,3), round(r2_sqrt, 3)),
                                                aux = {'Number of exps for analysis': len(self.tree2_cont.tree.get_children())},
                                                ask = True)
       
        #adding the analysis to main window
        self.callback(f'CDL Analysis {self.analysis_counter}', node.__dict__, node.text)
        self.analysis_counter += 1

    def on_focus_out(self, event):
        
        self.on_slider_move(event)
        self.on_slider_release(event)

    def on_slider_move(self, event):
        
        val = self.vline_pos.get()
        self.vline.set_xdata([val,val])
        self.canvas.draw_idle()

    def on_slider_release(self, *args):
        if hasattr(self, "scatter_plot"):
            self.scatter_plot.remove()
            del self.scatter_plot

        if hasattr(self, "regression_line"):
            self.regression_line.remove()
            del self.regression_line

        self.results, self.dataframe = self.calculate_difference()

    def calculate_difference(self, potential = None):
        #set collection for unique experiments, can store it beforehand to avoid doing this everytime!
        experiments = {line.experiment for line in self.ax1.get_lines() if line is not self.vline}

        if potential is None:
            potential = self.vline_pos.get()

        #important, this function now uses 'Vf' and 'Im' - unprocessed data. NEed to fix it later on
        line, integral, dataframe = calculate_ECSA_from_slope(experiments, potential, index = self.get_curve_variable())
        r_coefficient_squared = line[2]**2
        #self.ax2.scatter(dataframe.iloc[:,0], dataframe.iloc[:,1])
        self.plot_cdl(dataframe.iloc[:,0], dataframe.iloc[:,1])
        #self.ax2.scatter(dataframe.iloc[:,0], dataframe.iloc[:,2])
        print(line)
        self.plot_line(line[0], line[1], dataframe.iloc[:,0], label = f'r^2 = {round(r_coefficient_squared, 3)}')
        #self.plot_line(integral[0], integral[1], dataframe.iloc[:,0])

        return (line, integral), dataframe

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
            _, df = self.calculate_difference(potential = potential)
            current_differences = df.iloc[:,1]
            print(current_differences)
            result.append(current_differences)
        scanrates = df.iloc[:,0]
        df = pd.DataFrame(result, columns = scanrates, index = y)
        print(df)
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
        self.canvas.draw_idle()

    def plot_line(self, a, b, x, label):
        x_array = np.array(x)
        y_array = a * x_array + b

        if not hasattr(self, 'regression_line'):
            # Create the line ONCE, store the Line2D object
            (self.regression_line,) = self.ax2.plot(x_array, y_array, color="red", label = label)
        else:
            # Update existing line
            self.regression_line.set_xdata(x_array)
            self.regression_line.set_ydata(y_array)
        
        self.ax2.legend()
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
    
    def get_curve_variable(self):

        try:
            index = [int(self.curve_selection_var.get())]
        except:
            if self.curve_selection_var.get() == 'all':
                index = [0, 1, 2]
                print('Getting only 3 curves!!!!')
            
        return index

    def plot_previews(self, event):

        # Make sure we have a list to track preview lines
        if not hasattr(self, "preview_lines"):
            self.preview_lines = []

        # Remove old preview lines
        for line in self.preview_lines:
            if line in self.ax1.lines:
                line.remove()
        self.preview_lines.clear()

        try:
            preview_datasets = self.tree1_cont.get_experiments('selection')
        except:
            #print(print(self.tree1_cont.tree.item(self.tree1_cont.tree.selection(),'text')))
            return
        
        # Plot new previews
        for preview_dataset in preview_datasets:
            lines = plot_experiment(preview_dataset,
                                    self.ax1,
                                    self.canvas,
                                    x_column = 'E vs RHE [V]',
                                    y_column= 'I [A]',
                                    index = self.get_curve_variable(),
                                    alpha = 0.2)
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

        vline = getattr(self, 'vline', None)
        lines_to_remove = [line for line in self.ax1.get_lines() if line is not vline]
        for line in lines_to_remove:
            line.remove()
   
        experiments = self.tree2_cont.get_experiments('all')
        for experiment in experiments:
            plot_experiment(experiment,
                            self.ax1,
                            self.canvas,
                            x_column = 'E vs RHE [V]',
                            y_column = 'I [A]',
                            index = self.get_curve_variable(),
                            alpha = 1)

    def save_treeview(self, tree: ttk.Treeview):
        list_to_df = []
        for row_id in tree.get_children():
            row_item = tree.item(row_id, 'values')
            list_to_df.append(row_item)

        # Get column headings
        col_headings = [tree.heading(col)["text"] for col in tree["columns"]]    
        pd.DataFrame(list_to_df, columns = col_headings).to_excel('test.xlsx', engine = 'openpyxl')

    def alternate_method(self):
        experiments = self.tree2_cont.get_experiments('all')
        slopes, df = calculate_ECSA_from_slope(experiments, [self.vline_pos.get()])

    def get_dataframe_from_plot(self, *args):
        self.dataframe.to_clipboard()


if __name__ == "__main__":
    app = InteractivePlotApp()
    app.mainloop()