from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QTreeView, QListWidget, QListWidgetItem, QLabel, QShortcut, QMenu, QFileDialog
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from random import sample
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from .painting import create_line_icon, ColorManager
import pandas as pd
import matplotlib.dates as mdates
from functions.functions import calc_closest_2D
from experiments import Experiment

ColorRole = Qt.UserRole + 1

class PlottingCanvasTest(FigureCanvas):
    def __init__(self):
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)

    def plot_experiments(self, experiments_list=None):
        self.axes.clear()
        # Generujemy losowe dane do testu
        self.axes.plot(sample(range(1, 101), 10), sample(range(1, 101), 10), 'o-')
        self.draw()


class PlottingCanvas(FigureCanvas):
    def __init__(self):
        self.fig = Figure(figsize = (5, 4), dpi=100)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)

    def plot_experiments(self, experiments_list = None):
        self.axes.clear()
        for exp, color in experiments_list:
            if not hasattr(exp, 'data_list'):
                data = exp.load_curves()

            x, y = exp.get_default_columns('both')
            if not hasattr(exp, 'processed_data'):
                processed_data = exp.process_data()
            else:
                processed_data = getattr(exp, 'processed_data')
            self.axes.plot(processed_data[0][x], processed_data[0][y], color = color)

        self.draw()

    def plot(self, x, y):
        self.axes.plot(x, y)
        self.draw()


class OCPPlot(FigureCanvas):
    def __init__(self, figsize = (3,4), dpi = 100, label = None):
        self.fig = Figure(figsize = figsize, dpi = dpi)
        super().__init__(self.fig)

        # Axes settings
        self.label = label
        self.axes = self.fig.add_subplot(111)
        self.axes.set_title('Open Circuit Potential')
        self.axes.set_xlabel('Time [s]')
        self.axes.set_ylabel('OCP [V]')

        #crosshair
        self.v_line = self.axes.axvline(color = 'gray', linestyle="--", linewidth = 0.8, visible = False)
        self.h_line = self.axes.axhline(color = 'gray', linestyle="--", linewidth = 0.8, visible = False)

        #connecting functions
        self.fig.canvas.mpl_connect('button_release_event', self.on_release)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_movement)
        
    def on_movement(self, event):
        if not event.inaxes:
            self.v_line.set_visible(False)
            self.h_line.set_visible(False)
        else:
            self.v_line.set_visible(True)
            self.h_line.set_visible(True)
            self.v_line.set_xdata([event.xdata])
            self.h_line.set_ydata([event.ydata])
            self.draw_idle()

    def on_release(self, event):
        """A graph function that allows the user to pick a point on the OCP graph
        and visualize it on the top of the graph. The (x,y) coordinates are stored in picked_x and picked_y attributes."""

        # in case the user already pressed once, delete previous point
        if hasattr(self, 'selected_point'):
            self.selected_point.remove()

        #capturing the data coordinates which need to be normalized later on
        click_x = event.xdata
        click_y = event.ydata

        #grabbing full OCP data
        x_data = self.current_plot.get_xdata()
        y_data = self.current_plot.get_ydata()
        
        # the calc_closest_2D normalizees the x_data and y_data, so that it aligns with the place user pressed
        self.picked_x, self.picked_y = calc_closest_2D(x_data, y_data, click_x, click_y, self.axes)

        # plot is better than scatter, but needs the marker to do one point
        self.selected_point, = self.axes.plot(self.picked_x, self.picked_y, color = 'red', marker = 'o' , markersize = 5)

        #storing the result also in the label
        self.label.setText(f'Current point: {self.picked_x}, {self.picked_y}')
        self.draw_idle()
        
    def contextMenuEvent(self, event):
        menu = QMenu(self)

        action_save_graph = menu.addAction("Save the graph")
        action_copy_graph = menu.addAction("Copy numerical data")
        action_add_entry = menu.addAction("Add entry")

        action = menu.exec_(event.globalPos())

        if action == action_save_graph:
            path, _ = QFileDialog.getSaveFileName(
                self, "Save graph as", "", "PNG (*.png);;PDF (*.pdf);;All Files (*)"
            )
            if path:
                self.fig.savefig(path)

    def get_entry(self):
        if self.selected_point:
            return (self.picked_x, self.picked_y)
        else:
            return

    def plot_experiments(self, experiments_list: list[Experiment] = None):
        for exp in experiments_list:
            if not hasattr(exp, 'data_list'):
                data = exp.load_curves()

            x, y = exp.get_default_columns('both')
            if not hasattr(exp, 'processed_data'):
                processed_data = exp.process_data()
            else:
                processed_data = getattr(exp, 'processed_data')
            self.current_plot, = self.axes.plot(
            processed_data[0][x], 
            processed_data[0][y], 
            picker=5        # 10 pikseli tolerancji (liczba, nie True!)
            )
            
        self.draw()


    def plot(self, x, y):
        self.axes.plot(x, y)
        self.draw()

    def plot_df(self, df):
        self.axes.clear()
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        df.plot(ax = self.axes)
        self.axes.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        self.fig.autofmt_xdate() # Obraca daty
        self.axes.grid(True)
        self.axes.set_title("Pomiary elektrod")
        self.draw() # Odświeżamy Canvas


class MyListWidget(QListWidget):
    def __init__(self):
        super().__init__()
        self.counter = 0

    def get_current_index(self):
        counter_str = 'Plot ' + str(self.counter)
        self.counter += 1
        return counter_str

    def addItem(self, item):
        super().addItem(item)

class PlotManagerPanel(QWidget):
    def __init__(self,  canvas, parent = None,):
        super().__init__(parent)

        self.color_manager = ColorManager()
        self.canvas = canvas
        self.my_layout = QVBoxLayout(self)
        self.list_widget = MyListWidget()

        self.my_layout.addWidget(QLabel("Active Plots"))
        self.my_layout.addWidget(self.list_widget)
        btn =QPushButton("Delete")

        btn.clicked.connect(self.delete_plot)
        btn = self.my_layout.addWidget(btn)

        self.list_widget.itemChanged.connect(self.update_canvas)

        btn_delete_shortcut = QShortcut(QKeySequence("Delete"), self.list_widget)
        btn_delete_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        btn_delete_shortcut.activated.connect(self.delete_plot)    
        


    def add_plots(self, experiments):
        """
        Przyjmuje pojedynczy obiekt eksperymentu lub listę eksperymentów.
        """
        # Jeśli przekazano pojedynczy obiekt, zamień go w listę jednoelementową
        if not isinstance(experiments, list):
            experiments = [experiments]
        
        changed = False
        for exp in experiments:
            # Sprawdzenie duplikatów (Twoja świetna optymalizacja)
            already_exists = False
            for i in range(self.list_widget.count()):
                if self.list_widget.item(i).data(Qt.UserRole) == exp:
                    already_exists = True
                    break
            
            if not already_exists:
                
                name = self.list_widget.get_current_index()
                item = QListWidgetItem(name)
                item.setData(Qt.UserRole, exp)
                

                color = self.color_manager.get_next_color('List 1')
                item.setCheckState(Qt.CheckState.Checked)
                item.setIcon(create_line_icon(color))
                item.setData(ColorRole, color)

                self.list_widget.addItem(item)
                changed = True
                
        # Odświeżamy wykres tylko jeśli faktycznie coś dodano
        if changed:
            self.update_canvas()
    
    def delete_plot(self):
            print('elo')
            selected_items = self.list_widget.selectedItems()
            if not selected_items:
                return
                
            for item in selected_items:
                self.list_widget.takeItem(self.list_widget.row(item))
            
            # Po usunięciu zbieramy to, co zostało na liście i odświeżamy wykres
            self.update_canvas()

    def update_canvas(self):
        # Wyciągamy obiekty eksperymentów z pozostałych elementów listy
        remaining_experiments = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            exp = item.data(Qt.UserRole)
            color = item.data(ColorRole)

            if item.checkState() == Qt.CheckState.Checked:
                remaining_experiments.append((exp, color))
        
        print(remaining_experiments)
        # Wywołujemy rysowanie tylko tego, co zostało
        self.canvas.plot_experiments(remaining_experiments)


class PlottingArea(QWidget):
    def __init__(self):
        super().__init__()

        self.Canvas = PlottingCanvas()
        self.axes = self.Canvas.axes
        my_layout = QVBoxLayout()
        self.btn = QPushButton('Press to plot')

        my_layout.addWidget(self.Canvas)
        my_layout.addWidget(self.btn)

        self.setLayout(my_layout)

    def get_canvas(self):
        return self.Canvas

    def plot(self, df):     
        self.Canvas.plot(df)
    

