import tkinter as tk
from tkinter import ttk
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from numpy.random import rand
import numpy as np


class ChronoPicker(tk.Toplevel):
    def __init__(self, parent, nodes = None, callback = None, x = None, y = None):

        def on_click(event):
            if len(self.vlines) > 0:
                self.vlines[0].remove()
                self.vlines.pop()
            
            (plot, ) = self.first_plot
            x, y = plot.get_xdata(), plot.get_ydata()

            c = np.sqrt((event.xdata - x)**2 + (event.ydata - y)**2)
            index = np.argmin(c)
            test = self.ax.axvline(x[index], label = 'Dupa')
            print(f'Potential: {x[index]}, current: {y[index]}')
            self.vlines.append(test)
            self.canvas.draw_idle()
            

        super().__init__(parent)
        self.parent = parent
        self.nodes = nodes
        self.callback = callback
        self.vlines = []

        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        if (x is not None) and (y is not None):
            self.first_plot = self.ax.plot(x, y)
            self.canvas.mpl_connect('button_press_event', on_click)
        self.canvas.draw_idle()

    