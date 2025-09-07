import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from utilities.other import *
from gui.functions import delete_selected
import math

class InteractivePlotApp(tk.Toplevel):
    def __init__(self, parent):
        super().__init__()
        self.title("Interactive Vertical Line Plot")
        self.geometry("1000x1000")
        self.parent = parent
        self.nodes = []


        self.config_frame = ttk.Frame(self)
        self.config_frame.pack()

        self.data_treeview_label = ttk.Label(self.config_frame, text = 'Available experiments')
        self.data_treeview_label.grid(column = 0, row = 0)
        self.data_treeview = ttk.Treeview(self.config_frame)
        self.data_treeview.grid(column=0, row=1)
        self.data_treeview.bind("<<TreeviewSelect>>", self.plot_previews)


        ttk.Button(self.config_frame, text='Set line', command = self.set_lines).grid(column=1,row=2) 

        self.button_frame = ttk.Frame(self.config_frame)
        self.move_to_data_button = tk.Button(self.button_frame, text = '>>', command = lambda: self.move(self.data_treeview, self.analysis_treeview))
        self.move_to_data_button.grid(column = 0, row = 0, sticky = 'ns')
        self.move_to_analysis_button = tk.Button(self.button_frame, text = '<<', command = lambda: self.move(self.analysis_treeview, self.data_treeview))
        self.move_to_analysis_button.grid(column=0, row= 1, sticky = 'ns')
        self.button_frame.grid(column = 1, row = 1)


        self.data_treeview_label = ttk.Label(self.config_frame, text = 'To analysis')
        self.data_treeview_label.grid(column = 2, row = 0)
        self.analysis_treeview = ttk.Treeview(self.config_frame)
        self.analysis_treeview.grid(column=2, row = 1)


        self.plot_frame = ttk.Frame(self)
        self.plot_frame.pack(fill = tk.BOTH, expand = True)

        # Create figure
        self.fig, (self.ax1, self.ax2) = plt.subplots(nrows = 1, ncols = 2)

        self.ax1.set_xlabel("X")
        self.ax1.set_ylabel("Y")
        self.ax2.set_xlabel("Scanrate [mV/s]")
        #need to change the units on this thing!
        self.ax2.set_ylabel("J_GEO difference [A/cm2]")

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.draw_idle()

        # Label for info

        #Slider
        self.vline_pos = tk.DoubleVar()
        self.slider = ttk.Scale(self, from_=-1, to = 1, orient='horizontal', command=self.on_slider_move, value = 0, variable = self.vline_pos)
        self.slider.pack(padx=20, pady=10)
        self.slider.bind('<ButtonRelease-1>', self.on_slider_release)
        
        #entry (combined with slider)
        self.potential_entry = ttk.Entry(self, textvariable = self.vline_pos)
        self.potential_entry.pack()

        #Button to calculate difference
        self.button = ttk.Button(self.plot_frame, text = 'Calculate difference!', command = self.manual_update)
        self.button.pack()
        self.difference_info_label = ttk.Label(self.plot_frame, text = "0")
        self.difference_info_label.pack()
        
        self.analysis_list = []
        self.add_analysis_btn = ttk.Button(self, text = 'Add analysis', command = self.add_analysis)
        self.save_analysis_btn = ttk.Button(self, text = 'Save analysis', command = lambda: print(self.get_analysis()))
        self.add_analysis_btn.pack()
        self.save_analysis_btn.pack()

    def add_analysis(self):
        self.analysis_list.append(self.results)

    def get_analysis(self):
        return self.analysis_list

    def on_slider_move(self, val):
        val = float(val)
        print(val)
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
            print(f'difference: {difference}, scanrate: {scanrate}')
            scanrates.append(scanrate)
            current_differences.append(difference)

        return scanrates, current_differences

    def manual_update(self):
        self.on_slider_move(self.vline_pos.get())
        self.on_slider_release()


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


    def get_data(self, tree, selection_mode):
        nodes = get_treeview_nodes(tree, self.parent.manager, selection_mode)
        
        return nodes

    def set_lines(self):
        
        nodes = self.get_data(self.analysis_treeview, 'all')
        experiments = get_experiments_from_nodes(nodes)

        vline_min, vline_max = self.get_minmax_x(experiments)
        vline_position = vline_min + (vline_max - vline_min)/2
        self.slider.config(from_ = vline_min, to = vline_max)
        self.vline = self.ax1.axvline(x=vline_position, color='red', linestyle='--', label="Slider Position")
        self.vline.set_xdata([vline_position, vline_position])
        self.canvas.draw_idle()

        return 
    
    def plot_data(self):
        
        clear_plot(self.ax1)
        nodes = self.get_data(self.analysis_treeview, 'all')
        for node in nodes:
            plot_experiment(node, self.ax1, self.canvas, x_column = 'E vs RHE [V]', y_column = 'J_GEO [A/cm2]', alpha = 0.2)
    
    def plot_previews(self, event):
        # Make sure we have a list to track preview lines
        if not hasattr(self, "preview_lines"):
            self.preview_lines = []

        # Remove old preview lines
        for line in self.preview_lines:
            if line in self.ax1.lines:
                line.remove()
        self.preview_lines.clear()

        preview_datasets = self.get_data(self.data_treeview, 'selected')
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
            result = experiment.get_columns(axis = None, columns = ['E vs RHE [V]'])
            min_val = min(min_val, np.min(result))
            max_val = max(max_val, np.max(result))
            self.x = result

        return min_val, max_val

    def move(self, from_:ttk.Treeview, to:ttk.Treeview):

        for item_id in from_.selection():
            print(item_id)
            
            text = from_.item(item_id, 'text')
            values = from_.item(item_id, 'values')
            to.insert('', 'end', iid = item_id,  text = text, values = values)
            from_.delete(item_id)

        self.update_plot(self.ax1, self.analysis_treeview)

    def update_plot(self, ax, tree):
        ax.clear()
        nodes = get_treeview_nodes(tree, self.parent.manager, 'all')
        for node in nodes:
            plot_experiment(node, self.ax1, self.canvas, x_column = 'E vs RHE [V]', y_column = 'J_GEO [A/cm2]')
        self.ax.update()


if __name__ == "__main__":
    app = InteractivePlotApp()
    app.mainloop()