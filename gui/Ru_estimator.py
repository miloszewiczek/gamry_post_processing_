import tkinter as tk
from tkinter import ttk
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from .tree_controller import TreeController
from .slider import plot_experiment

class RuEstimate(tk.Toplevel):
    def __init__(self, parent, manager, loader, callback = None, nodes = None):
        super().__init__(parent)        

        self.title('Ru estimation')
        self.parent = parent
        self.manager = manager
        self.loader = loader
        self.callback = callback

        self.setup_gui(nodes = nodes)
    
    def setup_gui(self, nodes):

        self.canvas_frame = ttk.Frame(self)
        self.canvas_frame.grid(row = 0, column = 1)
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master = self.canvas_frame)
        self.canvas.get_tk_widget().pack(fill = tk.BOTH, expand = True)
        self.canvas.draw()
        self.ax.set_title(r'Interactive Ru estimation')
        self.ax.set_xlabel(r'$E_{iR}\  vs\  RHE\  [V]$')
        self.ax.set_ylabel(r'$Current\ I\  [A]$')

        self.config_frame = ttk.Frame(self)
        self.config_frame.grid(row = 0, column = 0, sticky = 'ns', padx = 5, pady = 5)
        self.tree = ttk.Treeview(self.config_frame)
        self.tree.pack(fill = tk.Y, expand = True)
        self.tree_controller = TreeController(self.loader, self.tree, self.manager, nodes = nodes)

        self.Ru_adjust_frame = ttk.Frame(self.config_frame)
        self.Ru_adjust_frame.pack(fill = tk.X, pady = 5)
        self.Ru_var = tk.DoubleVar(self, value = 0)
        self.Ru_scale = tk.Scale(self.Ru_adjust_frame, variable = self.Ru_var, from_ = 0, to = 100, resolution = 1, orient = 'horizontal')
        self.Ru_scale.bind('<ButtonRelease-1>', self.on_slider_release)
        self.Ru_scale.pack(side = tk.LEFT, expand = True, fill = tk.X, padx = 5)

        self.Ru_entry = ttk.Entry(self.Ru_adjust_frame, textvariable = self.Ru_var, width = 5, justify = 'center')
        self.Ru_entry.pack(side = tk.RIGHT, expand = False, padx = 5)


        self.plot_btn = ttk.Button(self.config_frame, text = 'Plot!', command = self.plot)
        self.plot_btn.pack()

        self.set_Ru_btn = ttk.Button(self.config_frame, text = 'Set', command = self.set_Ru)
        self.set_Ru_btn.pack()

    def plot(self):

        self.ax.clear()
        exps = self.tree_controller.get_experiments('selection')
        for exp in exps:
            current = exp.data_list[0].Im
            potential = exp.data_list[0].Vf
            self.ax.plot(potential, current)
            self.canvas.draw_idle()

    def on_slider_release(self, event):
        
        if not hasattr(self, 'preview_lines'): 
            self.preview_lines = []   
        
        for line in self.preview_lines:
            if line in self.ax.lines:
                line.remove()
        self.preview_lines.clear()

        line = self.ax.get_lines()[0]
        x_data = line.get_xdata()
        y_data = line.get_ydata()

        new_x_data = x_data - (self.Ru_var.get() * y_data)
        preview_line = self.ax.plot(new_x_data, y_data, label = str(self.Ru_var.get()))
        self.ax.legend()
        self.preview_lines.extend(preview_line)
        self.canvas.draw_idle()

    def set_Ru(self):
        self.callback(self.Ru_var.get())