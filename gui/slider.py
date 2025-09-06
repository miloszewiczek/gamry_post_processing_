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

        self.data_treeview = ttk.Treeview(self.config_frame)
        self.data_treeview.grid(column=0, row=0)
        self.data_treeview.bind("<<TreeviewSelect>>", self.plot_previews)


        ttk.Button(self.config_frame, text='setline', command = self.set_lines).grid(column=1,row=1) 
        ttk.Button(self.config_frame, text = 'plot!', command = self.plot_data).grid(column=1,row=2)

        self.analysis_list = ttk.Treeview(self.config_frame)
        self.analysis_list.grid(column=2, row = 0)
        self.move_to_data_button = tk.Button(self.config_frame, text = '>>', command = lambda: self.move(self.data_treeview, self.analysis_list))
        self.move_to_data_button.grid(column = 1, row = 0)
        self.move_to_analysis_button = tk.Button(self.config_frame, text = '<<', command = lambda: self.move(self.analysis_list, self.data_treeview))
        self.move_to_analysis_button.grid(column=1, row= 1)



        self.test = ttk.Button(self.config_frame, text = 'TESTING', command = self.get_data)
        self.test.grid(column=1,row=3)


        self.plot_frame = ttk.Frame(self)
        self.plot_frame.pack()

        # Create figure
        self.fig, (self.ax1, self.ax2) = plt.subplots(nrows = 1, ncols = 2)

        self.ax1.set_xlabel("X")
        self.ax1.set_ylabel("Y")

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.draw()

        # Label for info
        self.info_label = ttk.Label(self.plot_frame, text="X: 0.0 | Y: 0.0")
        self.info_label.pack()


        self.vline_pos = tk.DoubleVar()
        #Button to calculate difference
        self.button = ttk.Button(self.plot_frame, text = 'Calculate difference!', command = lambda: self.calculate_difference(self.vline_pos))
        self.button.pack()
        self.difference_info_label = ttk.Label(self.plot_frame, text = "0")
        self.difference_info_label.pack()
        

    def on_slider_move(self, val):
        val = float(val)
        print(val)
        self.vline.set_xdata([val,val])
        self.canvas.draw_idle()



    def calculate_difference(self, potential):
        nodes = self.get_data(self.analysis_list, 'all')
        experiments = get_experiments_from_nodes(nodes)
        for line in self.ax1.get_lines():
            x_data = line.get_xdata()
            y_data = line.get_ydata()
            print(x_data)

        #result = self.y_vals.diff().iloc[-1]
        #self.difference_info_label.config(text = f"{result}")
        
        #return result
    
    def get_data(self, tree, selection_mode):
        nodes = get_treeview_nodes(tree, self.parent.manager, selection_mode)
        print(nodes)
        return nodes

    def set_lines(self):
        
        nodes = self.get_data(self.analysis_list, 'all')
        experiments = get_experiments_from_nodes(nodes)

        vline_min, vline_max = self.get_minmax_x(experiments)
        vline_position = vline_min + (vline_max - vline_min)/2
        print(vline_position)

       
        self.slider = ttk.Scale(self, from_=vline_min, to = vline_max, orient='horizontal', command=self.on_slider_move, value = vline_position, variable = self.vline_pos)
        self.slider.pack(fill=tk.X, padx=20, pady=10)
        self.vline = self.ax1.axvline(x=vline_position, color='red', linestyle='--', label="Slider Position")
        self.on_slider_move(vline_position)

        return 
    
    def plot_data(self):
        
        clear_plot(self.ax1)
        nodes = self.get_data(self.analysis_list, 'all')
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
            print(self.preview_lines)

        self.canvas.draw()

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

        self.update_plot(self.ax1, self.analysis_list)

    def update_plot(self, ax, tree):
        ax.clear()
        nodes = get_treeview_nodes(tree, self.parent.manager, 'all')
        for node in nodes:
            plot_experiment(node, self.ax1, self.canvas, x_column = 'E vs RHE [V]', y_column = 'J_GEO [A/cm2]')
        self.ax.update()


if __name__ == "__main__":
    app = InteractivePlotApp()
    app.mainloop()