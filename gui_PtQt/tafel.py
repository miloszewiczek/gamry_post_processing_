import sys
from pathlib import Path
from PyQt5.QtWidgets import (QTreeWidget, QWidget, QLayout, QPushButton, QHBoxLayout, 
                             QVBoxLayout, QTreeView, QFileDialog, QMessageBox, 
                             QAbstractItemView, QDialog, QLabel, 
                             QFormLayout, QDialogButtonBox, QTableView,
                             QComboBox, QMenu, QTextBrowser, QShortcut, QInputDialog, QDoubleSpinBox, QLineEdit)
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QColor, QIcon, QKeySequence, QBrush
from PyQt5.QtCore import Qt, QAbstractTableModel, QItemSelection, QItemSelectionModel, QPersistentModelIndex, pyqtSignal, QModelIndex

from core import ExperimentLoader, ExperimentManager, Experiment
from functions.gui_functions import open_file_in_system_editor, open_folder_in_explorer
from functions.gui_functions import load_data, load_files, load_folder
from gui.calculate_diameter import AreaDialogBox, AreaDialog
from gui_PtQt.config import icon_path
from experiments.sample import Sample
from gui.small_widgets import TreeFilterProxyModel, SelectorWithSample
from experiments import LinearVoltammetry
from gui_PtQt.plotting_area import TafelCanvas
from numpy import gradient
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from functions.functions import calc_closest_value
from scipy.stats import linregress
from core import ExperimentManager



class TafelAnalysisWindow(QDialog):

    def __init__(self, selected_indices, parent=None, manager=None):
        super().__init__(parent)
        self.setWindowTitle("Tafel Analysis")
        self.resize(1400, 600)
        
        self.manager = manager
        
        # 1. Wstępne ładowanie i procesowanie surowych danych
        self.selector = SelectorWithSample(selected_indices)
        self.tafel_analyzer = TafelCoreWidget(manager = manager, parent = None)
        self.selector.flat_list_signal.connect(self.tafel_analyzer.set_experiments)
        # self.selector.item_changed.connect(self.tafel_analyzer.set_experiments)

        # Struktury do obsługi kolejki
        self.experiment_queue = []
        self.current_exp_index = 0
        self.analysis_results = {} # Tu zapiszemy wyniki dopasowań Tafel dla potomnych


        self._bootstrap_data(selected_indices)
        self.build_ui()

    def _bootstrap_data(self, selected_indices):
        """Wstępne ładowanie i procesowanie danych na bazie zaznaczonych indeksów."""
        for sample, experiments in selected_indices.items():
            for LSV_experiment in experiments:
                if isinstance(LSV_experiment, LinearVoltammetry):
                    if not hasattr(LSV_experiment, "data_list"):
                        LSV_experiment.load_all()
                    if not hasattr(LSV_experiment, 'processed_data'):
                        LSV_experiment.process_data()

    def build_ui(self):

        main_layout = QHBoxLayout()
        main_layout.addWidget(self.selector, stretch = 2)
        main_layout.addWidget(self.tafel_analyzer)
        self.setLayout(main_layout)


class TafelCoreWidget(QWidget):

    def __init__(self, manager:ExperimentManager, parent = None):
        # Wykres i toolbar pakujemy w jeden pionowy layout
        super().__init__(parent)

        self.manager = manager
        self.parent = parent
        self.canvas = TafelCanvas()

        self.plot_btn = QPushButton('Start Analysis Queue')
        self.plot_btn.clicked.connect(self.start_analysis_queue)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        self.experiments_dict = {}
        self.experiments = []
        self.current_exp_index = 0
        self.experiment_queue = []

        self.build_ui()


    def set_experiments(self, experiments):
        self.experiments = experiments
        self.experiments_dict = self.manager.construct_tree_with_cycles(experiments)
        
    def build_ui(self):
        
        plot_layout = QVBoxLayout()
        plot_layout.addWidget(self.canvas)
        plot_layout.addWidget(self.toolbar)
        plot_layout.addWidget(self.plot_btn)
        self.setLayout(plot_layout)



    def start_analysis_queue(self):
        """Buduje płaską kolejkę eksperymentów do analizy krok po kroku."""

        self.experiment_queue = []
        for sample, cycle_dict in self.experiments_dict.items():
            for cycle_num, exps in cycle_dict.items():
                for exp in exps:
                    # Zapisujemy tuple z obiektem i jego metadanymi
                    self.experiment_queue.append((sample, cycle_num, exp))
        
        if not self.experiment_queue:
            QMessageBox.warning(self, "Brak danych", "Kolejka eksperymentów jest pusta!")
            return
            
        self.current_exp_index = 0
        self.load_current_experiment()

    def load_current_experiment(self):
        """Ładuje i rysuje wykres dla bieżącego eksperymentu z kolejki."""
        if self.current_exp_index >= len(self.experiment_queue):
            QMessageBox.information(self, "Koniec", "Przeanalizowano wszystkie próbki z kolejki!")
            return

        sample, cycle_num, exp = self.experiment_queue[self.current_exp_index]
        
        self.setWindowTitle(f"Tafel Analysis - [{sample.sample_name}] Cykl {cycle_num} ({self.current_exp_index + 1}/{len(self.experiment_queue)})")
        self.get_data_from_experiment(exp)
        self.plot_on_canvas()
        self.setFocus()

    def get_data_from_experiment(self, experiment:LinearVoltammetry):

        self.current_x, self.current_y = experiment.get_xy_tafel_data(0)
        self.current_dy_dx = gradient(self.current_y, self.current_x)

    def plot_on_canvas(self):
        
        # --- KLUCZOWA ZMIANA ---
        # Zamiast self.canvas.tafel_cv.clear(), używamy selektywnego czyszczenia:
        self.canvas.clear_only_lines()

        # Rysujemy nowe dane na tych samych osiach
        self.canvas.plot_tafel(self.current_x, self.current_y)
        self.canvas.plot_derivative(self.current_x, self.current_dy_dx)
        
        # Wymuszamy automatyczne przeskalowanie osi do NOWYCH danych, 
        # bo bez .clear() Matplotlib mógłby pamiętać stare limity osi Y
        self.canvas.tafel_cv.relim()
        self.canvas.tafel_cv.autoscale_view(True, scalex=True, scaley=True)
        

    # --- KLUCZOWA ZMIANA: NADPISANIE OBSŁUGI KLAWIATURY ---
    def keyPressEvent(self, event):
        """Wymusza specyficzne akcje dla Enter oraz Escape, blokując domyślne zachowanie QDialog."""
        
        # 1. Obsługa ENTER / RETURN
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if not self.experiment_queue:
                event.ignore()
                return

            # Sprawdzamy czy użytkownik ruszył suwak (czy zakres istnieje)
            if getattr(self.canvas, 'current_range', None) is None:
                QMessageBox.warning(self, "Brak zaznaczenia", "Zaznacz najpierw zakres na wykresie za pomocą myszki!")
                return

            # Pobieramy zapamiętane granice z canvasu


            sample, cycle_num, exp = self.experiment_queue[self.current_exp_index]
            data = self.canvas.get_data()


            # moving on to next experiment
            self.current_exp_index += 1
            self.load_current_experiment()
            
            event.accept() # Informujemy system, że zdarzenie zostało skonsumowane

        # 2. Obsługa ESCAPE (Wyjście z okna)
        elif event.key() == Qt.Key_Escape:
            reply = QMessageBox.question(
                self, 'Wyjście', "Czy na pewno chcesz przerwać analizę i zamknąć okno?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.reject() # Bezpieczne zamknięcie okna QDialog bez akceptacji wyników
            else:
                event.ignore()

        else:
            # Ignorujemy wszystkie inne klawisze, żeby przypadkowe kliknięcia nic nie popsuły
            super().keyPressEvent(event)