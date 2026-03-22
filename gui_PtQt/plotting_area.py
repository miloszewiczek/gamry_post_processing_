from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QTreeView, QListWidget, QListWidgetItem, QLabel
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from random import sample
from PyQt5.QtCore import Qt
from .painting import create_line_icon, ColorManager

ColorRole = Qt.UserRole + 1

class PlottingCanvas(FigureCanvas):
    def __init__(self):
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)

    def plot_experiments(self, experiments_list=None):
        self.axes.clear()
        # Generujemy losowe dane do testu
        self.axes.plot(sample(range(1, 101), 10), sample(range(1, 101), 10), 'o-')
        self.draw()

class PlottingArea(QWidget): # Zmieniamy na QWidget, żeby zawierał Layout
    def __init__(self):
        super().__init__()
        
        # Tworzymy główny layout dla tego widgetu
        self.main_layout = QVBoxLayout(self)
        
        self.Canvas = PlottingCanvas()
        self.button_row = QHBoxLayout()

        btn = QPushButton('Press to plot')
        # Lambda odcina sygnał 'checked', więc do funkcji trafi None (domyślny)
        btn.clicked.connect(lambda: self.Canvas.plot_experiments())
        
        self.button_row.addWidget(btn)

        self.main_layout.addWidget(self.Canvas)
        self.main_layout.addLayout(self.button_row) # Ważne: addLayout!


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
        btn.setShortcut("Delete")
        btn = self.my_layout.addWidget(btn)

        self.list_widget.itemChanged.connect(self.update_canvas)
        


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
        my_layout = QVBoxLayout()
        self.btn = QPushButton('Press to plot')

        my_layout.addWidget(self.Canvas)
        my_layout.addWidget(self.btn)

        self.setLayout(my_layout)

    def get_canvas(self):
        return self.Canvas


        
    

