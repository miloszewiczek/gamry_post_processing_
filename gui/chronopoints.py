import tkinter as tk
from tkinter import ttk
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from gui import TreeController

class ChronoPicker(tk.Toplevel):
    def __init__(self, parent, nodes = None, callback = None, x = None, y = None):

        def on_click(event, exp, potential):
            if len(self.vlines) > 0:
                self.vlines.pop()
            
            plot= self.first_plot
            x, y = plot.get_xdata(), plot.get_ydata()

            c = np.sqrt((event.xdata - x)**2 + (event.ydata - y)**2)
            index = np.argmin(c)
            test = self.ax.axvline(x[index], label = 'Dupa')
            print(f'Potential: {x[index]}, current: {y[index]}')
            self.vlines.append(test)
            self.canvas.draw_idle()
            self.canvas.mpl_disconnect(self.cid)
            
            information = [x[index], y[index], potential[index]]
            self.analysis_dict[exp] = information
            print(self.data_treeview.selection())
            self.data_treeview.item(self.data_treeview.selection()[0], tags = ('analyzed',))

        def plot():
            self.ax.clear()
            self.current_id = int(self.data_treeview.selection()[0])
            experiments = self.data_treeview_controller.get_experiments('selection')
            #grab first experiment
            exp = experiments[0]
            name = exp.file_name
            data = exp.get_columns(0, columns = ['T [s]', 'J_GEO [A/cm2]'])
            x = data['T [s]']
            y = data['J_GEO [A/cm2]']
            potential = exp.get_columns(0 , columns = ['E_iR vs RHE [V]'])
            if potential is None:
                potential = exp.get_columns(0 , columns = ['E vs RHE [V]'])
            potential = np.asarray(potential).flatten()
            
        
            (line,) = self.ax.plot(x, y)
            self.first_plot = line
            self.canvas.draw_idle()
            self.cid = self.canvas.mpl_connect('button_press_event', lambda event: on_click(event, name, potential))
        
        def next():
            self.ax.clear()
            self.data_treeview.selection_set(self.current_id + 1)
            plot()


        super().__init__(parent)
        self.parent = parent
        self.nodes = nodes
        self.callback = callback
        self.vlines = []
        self.analysis_dict = {}


        self.data_treeview = ttk.Treeview(self)
        self.data_treeview.tag_configure('analyzed', background='#d1ffd1', foreground='black')   # light green
        self.data_treeview.pack()
        self.data_treeview_controller = TreeController(parent.loader, self.data_treeview, parent.manager)
        self.data_treeview_controller.initialize_tree(nodes = nodes)

        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        if (x is not None) and (y is not None):
            self.first_plot = self.ax.plot(x, y)
            self.canvas.mpl_connect('button_press_event', on_click)
        self.canvas.draw_idle()


        
        self.plot_btn = ttk.Button(self, command = plot, text = 'plot')
        self.plot_btn.pack()

        ttk.Button(self, command = lambda: print(self.analysis_dict), text = 'Show dict').pack()
        ttk.Button(self, command = next, text = 'next plot').pack()    