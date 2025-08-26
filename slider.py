import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from utilities.other import *

class InteractivePlotApp(tk.Toplevel):
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
        self.data_treeview.bind("<<TreeviewSelect>>", self.plot_previews)


        ttk.Button(self.config_frame, text='setline', command = self.set_lines).grid(column=1,row=1) 
        ttk.Button(self.config_frame, text = 'plot!', command = self.plot_data).grid(column=1,row=2)

        self.analysis_list = ttk.Treeview(self.config_frame)
        self.analysis_list.grid(column=2, row = 0)
        self.add_to_analysis_button = tk.Button(self.config_frame, text = '>>', command = self.add_to_analysis)
        self.add_to_analysis_button.grid(column=1, row=0)
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

        # Label for info
        self.info_label = ttk.Label(self.plot_frame, text="X: 0.0 | Y: 0.0")
        self.info_label.pack()

        #Button to calculate difference
        self.button = ttk.Button(self.plot_frame, text = 'Calculate difference!', command = self.calculate_difference)
        self.button.pack()
        self.difference_info_label = ttk.Label(self.plot_frame, text = "0")
        self.difference_info_label.pack()
        

    def on_slider_move(self, val):
        val = float(val)
        self.vline.set_xdata([val,val])

        # Get nearest index
        idx = np.searchsorted(self.x, val)
        tolerance = (self.x.max() - self.x.min()) / len(self.x)  # one "step"
        mask = np.abs(self.x - val) < tolerance
        y_vals = self.y[mask]
        x_vals = self.x[mask]
        self.y_vals = y_vals

        if len(y_vals) > 0:
            self.markers.set_data(x_vals, y_vals)
            y_str = ", ".join([f"{y:.4f}" for y in y_vals])
            self.info_label.config(text=f"X ≈ {val:.3f} | Y: [{y_str}]")
        else:
            self.markers.set_data([], [])
            self.info_label.config(text=f"X ≈ {val:.3f} | Y: [no match]")

        self.canvas.draw_idle()

    def calculate_difference(self):
        result = self.y_vals.diff().iloc[-1]
        self.difference_info_label.config(text = f"{result}")
        
        return result
    
    def get_data(self):

        experiment_dicts = get_treeview_experiments(self.data_treeview, 'selected')
        experiment_dicts = map_ids_to_experiments(experiment_dicts, manager = self.parent.manager)
        return experiment_dicts

    def set_lines(self):
        
        vline_min, vline_max = self.get_minmax_x()
        vline_position = vline_min + (vline_max - vline_min)/2
        self.slider = ttk.Scale(self, from_=vline_min, to = vline_max, orient='horizontal', command=self.on_slider_move, value = vline_position)
        self.slider.pack(fill=tk.X, padx=20, pady=10)
        self.vline = self.ax.axvline(x=vline_position, color='red', linestyle='--', label="Slider Position")
        self.markers, = self.ax.plot([], [], 'ro')  # multiple points

        #self.on_slider_move(vline_position)
        return 
    
    def plot_data(self):
        
        experiment_dicts = self.get_data()
        for experiment_dict in experiment_dicts:
            plot_experiment(experiment_dict, self.ax, self.canvas, x_column = 'E vs RHE [V]', y_column = 'J_GEO [A/cm2]', alpha = 0.2)
    
    def plot_previews(self, event):
        # Make sure we have a list to track preview lines
        if not hasattr(self, "preview_lines"):
            self.preview_lines = []

        # Remove old preview lines
        for line in self.preview_lines:
            if line in self.ax.lines:
                line.remove()
        self.preview_lines.clear()

        preview_datasets = self.get_data()
        # Plot new previews
        for preview_dataset in preview_datasets:
            lines = plot_experiment(preview_dataset, self.ax, self.canvas, x_column = 'E vs RHE [V]', y_column= 'J_GEO [A/cm2]', alpha = 0.2)
            self.preview_lines.extend(lines)
            print(self.preview_lines)

        self.canvas.draw()

    def get_minmax_x(self):
        
        x, y = zip(*self.xy_data)
        x_min = np.min(x)
        x_max = np.max(x)

        return x_min, x_max

    def add_to_analysis(self):

        for item_id in self.data_treeview.selection():
            tmp, parents = get_tree_level(self.data_treeview, item_id, True)
            text = self.data_treeview.item(item_id, 'text')
            text = parents + "." + text
            values = self.data_treeview.item(item_id, 'values')
            self.analysis_list.insert('', 'end', text = text, values = values)


if __name__ == "__main__":
    app = InteractivePlotApp()
    app.mainloop()