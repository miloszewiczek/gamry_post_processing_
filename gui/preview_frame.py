import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib import pyplot as plt
from .functions import plot_selected

class PreviewImageFrame(tk.Frame):   
    def __init__(self, parent):
        super().__init__(parent)
        self.manager = parent.manager
        self.loader = parent.loader
        self.preview_tree = parent.filtered_tree
    
        #PREVIEW FIGURE
        self.preview_figure, self.preview_ax = plt.subplots()
        self.preview_figure.set_size_inches(5,5)
        self.preview_ax.set_position((0.15,0.15, 0.75, 0.75))
        self.preview_canvas = FigureCanvasTkAgg(self.preview_figure, self)
        self.preview_canvas.get_tk_widget().pack()
        toolbar = NavigationToolbar2Tk(self.preview_canvas, self)
        toolbar.update()
        self.preview_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        tk.Button(self, text = 'Plot selected', command = lambda: plot_selected(self.preview_tree, self.manager, self.preview_ax, self.preview_canvas )).pack()