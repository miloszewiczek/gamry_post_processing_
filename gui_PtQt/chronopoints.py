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
from core.functions.gui_functions import open_file_in_system_editor, open_folder_in_explorer
from core.functions.gui_functions import load_data, load_files, load_folder
from gui_PtQt.calculate_diameter import AreaDialogBox, AreaDialog
from gui_PtQt.configuration.config import icon_path
from core.experiments.sample import Sample
from gui_PtQt.small_widgets import TreeFilterProxyModel, SelectorWithSample
from core.experiments import LinearVoltammetry
from gui_PtQt.plotting_area import ChronopointCanvas
from numpy import gradient
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from scipy.stats import linregress
from .tafel import TafelCoreWidget
from core.experiments import Chronoamperometry
from core import analysis_manager

class ChronopointsCoreWidget(TafelCoreWidget):
    def __init__(self, manager, parent):
        super().__init__(manager, parent, canvas_type = ChronopointCanvas)
        self.canvas: ChronopointCanvas
        self.stored_points = []
        self.default_analysis_prefix = 'Chronop'

    
    def _bootstrap_data(self, selected_indices):
        return super()._bootstrap_data(selected_indices, Chronoamperometry)
    
    def get_data_from_experiment(self, experiment:Chronoamperometry):
        self.current_x, self.current_y = experiment.get_xy_data(0)

    def plot_on_canvas(self):
        self.canvas.plot_chrono(self.current_x, self.current_y)
    
    def create_analysis(self):
        from core.experiments.analysis import ChronopointAnalysis

        data_to_add = self.make_row_multiindex(self.data, columns = ['T [s]', 'J_GEO [A/cm2]']) 
        print(data_to_add)

        name = analysis_manager.ask_for_analysis_name(self.default_analysis_prefix)
        if name:
            analysis = ChronopointAnalysis(name = name, experiments = self.experiments, data = data_to_add)
            analysis_manager.add_analysis(analysis)



class ChronopointsAnalysisWindow(QDialog):

    def __init__(self, selected_indices, parent=None, manager=None):
        super().__init__(parent)
        self.setWindowTitle("ChronoPoint Analysis")
        self.resize(1400, 600)
        
        self.manager = manager
        
        # 1. Wstępne ładowanie i procesowanie surowych danych
        self.selector = SelectorWithSample(selected_indices)
        self.chronop_analyzer = ChronopointsCoreWidget(manager = manager, parent = None)
        self.selector.flat_list_signal.connect(self.chronop_analyzer.set_experiments)
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
        main_layout.addWidget(self.chronop_analyzer)
        self.setLayout(main_layout)

    
