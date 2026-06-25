from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QTreeView, QListWidget, QListWidgetItem, QLabel, QShortcut, QMenu, QFileDialog
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from random import sample
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QKeySequence, QColor
from .painting import create_line_icon, ColorManager
import pandas as pd
import matplotlib.dates as mdates
from core.functions.functions import calc_closest_2D
from core.experiments import Experiment
from matplotlib.widgets import SpanSelector
from scipy.stats import linregress
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar



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

    data_requested = pyqtSignal(list)

    def __init__(self, toolbar = False):
        self.fig = Figure(figsize = (5, 4), dpi=100)
        super().__init__(self.fig)
        self.axes = self.fig.add_subplot(111)
        self.selected_point_scatter = None
        self.selected_point_annotate = None
        if toolbar:
            self.setup_toolbar()


    def setup_toolbar(self):
        self.toolbar = NavigationToolbar(self)
    
    def get_toolbar(self):
        if hasattr(self, 'toolbar'):
            return self.toolbar
        else:
            print('No toolbar. Please add one using setup_toolbar.')
            return


    def plot_experiments(self, experiments_list: list[tuple[Experiment, QColor]] = None):
        self.axes.clear()
        
        if experiments_list:
            for exp, color in experiments_list:
                # Wywołujemy nową, mądrzejszą metodę z klasy Experiment
                exp.plot(ax=self.axes, color=color)
            
            # Dodatki estetyczne, o których Experiment nie musi wiedzieć
            self.axes.set_xlabel(experiments_list[0][0].default_x_plot)
            self.axes.set_ylabel(experiments_list[0][0].default_y_plot)
            self.axes.grid(True, alpha=0.3)
            # self.axes.legend() # Opcjonalnie

        self.draw_idle()

    def plot_experiments_no_color(self, experiments_list: list[Experiment] = None, curves = None, **kwargs):
        self.axes.clear()
        self.selected_point_scatter = None
        self.selected_point_annotate = None

        if experiments_list:
            if not isinstance(experiments_list, list):
                experiments_list = [experiments_list]

            for exp in experiments_list:
                # Wywołujemy nową, mądrzejszą metodę z klasy Experiment
                exp.plot(ax=self.axes, curves = curves, **kwargs)
            
            # Dodatki estetyczne, o których Experiment nie musi wiedzieć
            self.axes.set_xlabel(experiments_list[0].default_x_plot)
            self.axes.set_ylabel(experiments_list[0].default_y_plot)
            self.axes.grid(True, alpha=0.3)
            # self.axes.legend() # Opcjonalnie

        self.draw_idle()

        self.mpl_connect('button_release_event', self.onclick)

    def clear(self):
        self.axes.clear()

    def remove_lines(self):
        current_lines = self.axes.lines
        legend = self.axes.get_legend()
        if legend:
            legend.remove()
        while current_lines:
            current_lines[0].remove()

    def onclick(self, event):
        if (self.selected_point_scatter is not None) and (self.selected_point_annotate is not None):
            self.selected_point_scatter.remove()
            self.selected_point_annotate.remove()

        if event.inaxes:
            x, y  = self.axes.lines[0].get_data()
            self.selected_x, self.selected_y = calc_closest_2D(x, y, event.xdata, event.ydata, self.axes)
            self.selected_point_scatter = self.axes.scatter([self.selected_x], [self.selected_y], facecolors = 'none', color = 'red')
            self.selected_point_annotate = self.axes.annotate(f'{self.selected_x}', (self.selected_x, self.selected_y))
            self.draw_idle()

    def get_selected_point(self):
        return (self.selected_x, self.selected_y)

class OCPPlot(FigureCanvas):
    def __init__(self, figsize = (3,4), dpi = 100, label = None):
        self.fig = Figure(figsize = figsize, dpi = dpi)
        super().__init__(self.fig)

        self.toolbar = NavigationToolbar(self)
        # Axes settings
        self.label = label
        self.axes = self.fig.add_subplot(111)
        self.axes.set_title('Open Circuit Potential')
        self.axes.set_xlabel('Time [s]')
        self.axes.set_ylabel('OCP [V]')

        #crosshair
        self.v_line = self.axes.axvline(color = 'gray', linestyle="--", linewidth = 0.8, visible = False)
        self.h_line = self.axes.axhline(color = 'gray', linestyle="--", linewidth = 0.8, visible = False)


    
    def activate(self, event, button, callback = None):
        
        #connecting functions
        self.button_to_release = button
        self.callback = callback

        self.cids = [self.fig.canvas.mpl_connect('button_release_event', self.on_release),
                    self.fig.canvas.mpl_connect('motion_notify_event', self.on_movement)]
        
    
    def deactivate(self, event):
        for cid in self.cids:
            self.fig.canvas.mpl_disconnect(cid)
        del self.cids
        print(event)

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

        self.button_to_release.setEnabled(True)
        self.callback()
        self.deactivate(event)
        
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
        if hasattr(self, 'selected_point'):
            return (self.picked_x, self.picked_y)
        else:
            return

    def plot_experiments(self, experiments_list: list[Experiment] = None):
        if hasattr(self, 'current_plot'):
            self.current_plot.remove()

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
        
        self.axes.relim()
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
    plotsUpdated = pyqtSignal(list)

    def __init__(self, parent = None,):
        super().__init__(parent)

        self.color_manager = ColorManager()
        self.my_layout = QVBoxLayout(self)
        self.list_widget = MyListWidget()

        self.my_layout.addWidget(QLabel("Active Plots"))
        self.my_layout.addWidget(self.list_widget)
        btn = QPushButton("Delete")

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
            selected_items = self.list_widget.selectedItems()
            if not selected_items:
                return
                
            for item in selected_items:
                self.list_widget.takeItem(self.list_widget.row(item))
            
            # Po usunięciu zbieramy to, co zostało na liście i odświeżamy wykres
            self.update_canvas()

    def update_canvas(self):
        remaining_experiments = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                remaining_experiments.append((item.data(Qt.UserRole), item.data(ColorRole)))
        
        self.plotsUpdated.emit(remaining_experiments)


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
    

class DoubleLayerCanvas(FigureCanvas):
    data_requested = pyqtSignal(list)

    def __init__(self):
        # Tworzymy figurę o panoramicznych proporcjach pod dwa wykresy obok siebie
        self.fig = Figure(figsize=(10, 4.5), dpi=100)
        super().__init__(self.fig)
        
        self.toolbar = NavigationToolbar(self)

        # Tworzymy od razu 2 podwykresy (1 wiersz, 2 kolumny)
        self.ax_cv, self.ax_cdl = self.fig.subplots(1, 2)
        
        # Inicjalne przygotowanie osi (żeby okno nie było puste na starcie)
        self.clear_all()

    def clear_all(self):
        """Resetuje oba wykresy i nakłada domyślne siatki."""
        self.ax_cv.clear()
        self.ax_cdl.clear()
        
        self.ax_cv.set_title("Cyclic Voltammetry")
        self.ax_cv.grid(True, alpha=0.3)
        
        self.ax_cdl.set_title("$C_{dl}$ Linear Fit")
        self.ax_cdl.grid(True, alpha=0.3)
        
        self.v_line = self.ax_cv.axvline(color='gray', linestyle="--", linewidth=0.8, visible=True)
        self.fig.tight_layout()
        self.draw_idle()

    def clear_except_line(self):
        for line in self.ax_cv.lines[:]:  # [:] tworzy bezpieczną kopię listy do iteracji
            if line is not self.v_line:
                line.remove()  # Usuwa linię fizycznie z wykresu

    def plot_cv_curves(self, experiments_dict: dict[Experiment, list[pd.DataFrame]], **kwargs):
        """Rysuje TYLKO lewy wykres z woltamperometrią."""
        self.ax_cv.set_title("Cyclic Voltammetry")
        self.ax_cv.grid(True, alpha=0.3)

        first_exp = list(experiments_dict.keys())[0]
        self.ax_cv.set_xlabel(first_exp.default_x_plot)
        self.ax_cv.set_ylabel(first_exp.default_y_plot)

        if experiments_dict:
            for experiment, data in experiments_dict.items():
                for df in data:
                    self.ax_cv.plot(df.iloc[:,0], df.iloc[:,1], label = 'Dupa', **kwargs)
            
        self.move_vline(first_exp.get_half_potential())
        self.ax_cv.relim()
        self.ax_cv.autoscale_view()
        self.fig.tight_layout()
        self.draw_idle()

    def plot_cdl_fit(self, sample:str, data, clear = False, **kwargs):
        """Rysuje TYLKO prawy wykres na podstawie wyników z funkcji obliczeniowej."""
        if clear == True:
            self.ax_cdl.clear()
        self.ax_cdl.set_title("$C_{dl}$ Linear Fit")
        self.ax_cdl.grid(True, alpha=0.3)

        # BEZPIECZNE SPRAWDZENIE: 
        # Jeśli dostaliśmy pojedynczy DataFrame, zamieniamy go w listę jednoelementową.
        # Sprawdzanie pustki robimy za pomocą właściwości .empty dedykowanej dla Pandasa.
        if isinstance(data, pd.DataFrame):
            if data.empty:
                self.draw_idle()
                return
            data = [data]
        
        # Jeśli to zwykła lista i jest pusta
        elif not data:
            self.draw_idle()
            return

        #Right now it's only 1 dataframe. Need to fix it TODO.


        df = data['df_data']
        fitting_data_df = data['df_fitting']
        slope = fitting_data_df['Slope'].iloc[0]
        r_square = fitting_data_df['R^2'].iloc[0]

        # 1. Rysujemy punkty pomiarowe (Scanrate vs Difference)
        self.ax_cdl.plot(
            df['Scanrate [V/s]'], 
            df['Difference [A]'], 
            'o', 
            **kwargs
        )
        # 2. Rysujemy dopasowaną prostą regresji
        self.ax_cdl.plot(
            df['Scanrate [V/s]'], 
            df['Line fit [A]'], 
            '--', 
            label=f'{sample}\nSlope: {slope:.2e}, r$^2$ = {r_square:.2f}',
            **kwargs
        )

        self.ax_cdl.set_xlabel("Scan rate [V/s]")
        self.ax_cdl.set_ylabel("Current Difference $\Delta I$ [A]")
        self.ax_cdl.legend()
        
        self.fig.tight_layout()
        self.draw_idle()

    def move_vline(self, position):

        if self.v_line is None:
            return
        
        try:
            self.v_line.set_xdata([position, position])
            self.draw_idle()
        except:
            return


class TafelCanvas(FigureCanvas):
    data_requested = pyqtSignal(list)
    range_selected = pyqtSignal(float, float)

    def __init__(self):
        self.fig = Figure(figsize=(10, 6), dpi=100) # Zwiększyłem trochę wysokość pod 2 wykresy pionowo
        super().__init__(self.fig)
        
        # Tworzymy pierwszy wykres (górny)
        self.tafel_cv = self.fig.add_subplot(2, 1, 1)
        self.regression_line = None
        self.toolbar = NavigationToolbar(self)

        # Tworzymy drugi wykres (dolny) i łączymy oś X z górnym
        self.tafel_derivative = self.fig.add_subplot(2, 1, 2, sharex=self.tafel_cv)
        self.bottom_highlight = None
        # Opcjonalnie: ukrywa powtarzające się etykiety osi X na górnym wykresie
        # dzięki czemu wykresy ładniej do siebie przylegają
        self.tafel_cv.tick_params(labelbottom=False)
        # Będzie działał na osi X wykresu tafel_cv
        self.current_range = None  # Tu będziemy trzymać krotkę (xmin, xmax)
        self.span_selector = SpanSelector(
            ax=self.tafel_cv,
            onselect=self._on_span_select,
            direction="horizontal",
            useblit=True,
            props=dict(alpha=0.3, facecolor="orange"),
            interactive=True
        )
    def _on_span_select(self, xmin: float, xmax: float):
        # 1. Odświeżamy prostokąt na dolnym wykresie (tak jak ostatnio ustaliliśmy)
        if self.bottom_highlight is not None:
            self.bottom_highlight.remove()
        self.bottom_highlight = self.tafel_derivative.axvspan(xmin, xmax, facecolor="orange", alpha=0.3)
        self.draw_idle()
        
        # 2. ZAPISUJEMY wybrany zakres do pamięci zamiast od razu emitować sygnał analizy
        self.current_range = (xmin, xmax)
        to_tafel_range = (self.current_x >= xmin) & (self.current_x <= xmax)
        self.selected_x = self.current_x[to_tafel_range]
        self.selected_y = self.current_y[to_tafel_range]
        regression = linregress(self.selected_x, self.selected_y)
        self.current_slope = abs(regression.slope)
        self.tafel_cv.set_title(f'Calculated slope: {round(self.current_slope * 1000, 0)} mV/dec')

        if self.regression_line is not None:
            self.regression_line.remove()
        self.regression_line_data = self.selected_x * regression.slope + regression.intercept
        self.regression_line, = self.tafel_cv.plot(self.selected_x, self.regression_line_data, linewidth = 5, color = 'red')

    def plot_tafel(self, x, y):
        
        self.tafel_cv.set_title('Select data')
        self.current_x = x
        self.current_y = y

        self.tafel_cv.plot(x, y, color = 'blue')
        self.draw_idle()
        return x, y

    def plot_derivative(self, x, dy_dx):
        # Mnożymy przez 1e6, żeby przejść z amperów na mikroampery
        self.current_dy_dx = dy_dx

        self.tafel_derivative.plot(x, dy_dx, color = 'blue')
        self.tafel_derivative.set_ylim(-1, 1)
        self.draw_idle()


    def clear_only_lines(self):
        """Usuwa z obu wykresów tylko narysowane linie (wykresy), pozostawiając tło i prostokąty."""
        # Usuwamy linie z górnego wykresu
        while self.tafel_cv.lines:
            self.tafel_cv.lines[0].remove()
            
        # Usuwamy linie z dolnego wykresu
        while self.tafel_derivative.lines:
            self.tafel_derivative.lines[0].remove()
            
        self.regression_line = None
        # Odświeżamy widok, żeby stare linie zniknęły
        self.draw_idle()

    def get_data(self):
        return {'Slope': self.current_slope,
                'Selected xy': pd.concat((self.selected_x,self.selected_y), axis = 1),
                'Raw xy': pd.concat((self.current_x, self.current_y), axis =1),
                'Regression line': pd.concat((self.current_x, self.regression_line_data), axis = 1)}

    @property
    def isSelected(self):
        if self.regression_line:
            return True
        else:
            return False
    

class ChronopointCanvas(FigureCanvas):
    def __init__(self, storage = None):
        self.fig = Figure(figsize=(10, 6), dpi=100) # Zwiększyłem trochę wysokość pod 2 wykresy pionowo
        super().__init__(self.fig)
        
        self.ax = self.fig.add_subplot(1,1,1)
        self.ax.set_xlabel('T [s]')
        self.ax.set_ylabel('$j_{GEO}$ [A/cm²]')

        self.callback = storage
        self.toolbar = NavigationToolbar(self)


        super().__init__(self.fig)
        self.selected_point = None
        self.fig.canvas.mpl_connect('button_release_event', self.on_click)
    
    def plot_chrono(self, x,y):

        self.clear_lines(self.ax)

        self.ax.set_title('Select a point and click Enter')
        self.ax.plot(x,y, color = 'blue')
        self.ax.relim()
        self.fig.tight_layout()

        self.current_x = x
        self.current_y = y
        self.draw_idle()

    def on_click(self, event):
        
        if event.inaxes != self.ax:
            return
        if self.selected_point:
            self.selected_point.remove()
        
        x = event.xdata
        y = event.ydata
        self.selected_x, self.selected_y = calc_closest_2D(self.current_x, self.current_y, x, y, self.ax)
        self.selected_point, = self.ax.plot([self.selected_x], [self.selected_y], 'ro', markersize = 8)
        self.ax.set_title(f'Time: {self.selected_x}   Current density: {round(self.selected_y*1000, 2)} [mA/cm²]')


        if self.callback:
            self.callback()

        self.draw_idle()


    def clear_lines(self, ax):
    # Usuwamy linie z dolnego wykresu
        while ax.lines:
            ax.lines[0].remove()
        self.selected_point = None

    @property
    def isSelected(self):
        if self.selected_point:
            return True
        else:
            return False

    def get_data(self):
        return self.selected_x, self.selected_y



# for future
from typing import Dict, Type
canvas_registry: Dict[str, Type[QWidget]] = {
    "tafel", TafelCanvas
}