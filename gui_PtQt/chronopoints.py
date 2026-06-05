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
from gui_PtQt.plotting_area import ChronopointCanvas
from numpy import gradient
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from scipy.stats import linregress
from .base_analysis_window import BaseAnalysisWindow
from experiments import Chronoamperometry

class ChronopointsWindow(BaseAnalysisWindow):
    def __init__(self, items, parent = None, manager = None):
        super().__init__(items, parent, manager)
        self.canvas: ChronopointCanvas

    def create_canvas(self):
        return ChronopointCanvas()
    
    def _bootstrap_data(self, selected_indices):
        return super()._bootstrap_data(selected_indices, Chronoamperometry)
    
    def get_data_from_experiment(self, experiment:Chronoamperometry):
        self.current_x, self.current_y = experiment.get_xy_data(0)

    def plot_on_canvas(self):
        self.canvas.plot_chrono(self.current_x, self.current_y)

    def get_data(self):
        data = self.canvas.get_data()
        return data