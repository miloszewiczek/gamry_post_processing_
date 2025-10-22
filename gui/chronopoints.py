import tkinter as tk
from tkinter import ttk
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter.messagebox import askyesno
import numpy as np
from gui import TreeController, AnalysisTree

class ChronoPicker(tk.Toplevel):
    def __init__(self, parent, nodes = None, callback = None, x = None, y = None):

        def on_click(event, exp, potential, iRdrop):
            if len(self.vlines) > 0:
                self.vlines.pop()
            
            plot= self.first_plot
            x, y = plot.get_xdata(), plot.get_ydata()

            c = np.sqrt((event.xdata - x)**2 + (event.ydata - y)**2)
            index = np.argmin(c)
            test = self.ax.axvline(x[index], label = 'Dupa')
            self.vlines.append(test)
            self.canvas.draw_idle()
            self.canvas.mpl_disconnect(self.cid)
            
            information = (potential[index], x[index], y[index], iRdrop)
            selection_id = self.data_treeview.selection()[0]
            
            self.data_treeview.item(selection_id, tags = ('analyzed',))
            self.analysis_treeview.add_analysis(information, name = exp)

            #to be implemented
            '''
            if selection_id in self.analysis_dict:
                question = askyesno('Replace', 'There is already an analysis for this file. Replace? If no, it will be appended')
                if question is True:
                    self.analysis_treeview.tree.item(selection_id, values = information)
                else:
                    self.analysis_treeview.add_analysis(information, name = exp)
            else:
                self.analysis_treeview.add_analysis(information, name = exp)
            self.analysis_dict[selection_id] = information    
            '''

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
            iRdrop = True
            if potential is None:
                potential = exp.get_columns(0 , columns = ['E vs RHE [V]'])
                iRdrop = False
            potential = np.asarray(potential).flatten()
            
        
            (line,) = self.ax.plot(x, y)
            self.first_plot = line
            self.canvas.draw_idle()
            self.cid = self.canvas.mpl_connect('button_press_event', lambda event: on_click(event, name, potential, iRdrop))
        
        def next():
            next_id = self.current_id + 1
            maximum = max([int(child) for child in self.data_treeview.get_children()])
            if self.current_id >= maximum:
                return
            self.data_treeview.selection_set(next_id)
            plot()
            return next_id
        
        def previous():
            previous_id = self.current_id - 1
            minimum = min([int(child) for child in self.data_treeview.get_children()])
            if self.current_id <= minimum:
                return 
            self.data_treeview.selection_set(previous_id)
            plot()
            return previous_id


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

        self.analysis_treeview = AnalysisTree(self, 
                                              columns = ('E', 'T', 'J', 'Ru'),
                                              headers = ('E vs RHE [V]', 'T [s]', 'J GEO [A/cm2]', 'Ru?'),
                                              sizes = (75, 75, 75, 75, 75))
        self.analysis_treeview.pack()

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
        ttk.Button(self, command = next, text = '>').pack()    
        ttk.Button(self, command = previous, text = '<').pack()    
