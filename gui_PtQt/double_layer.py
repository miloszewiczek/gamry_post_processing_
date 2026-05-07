from PyQt5.QtWidgets import (QTreeWidget, QWidget, QLayout, QPushButton, QHBoxLayout, 
                             QVBoxLayout, QTreeView, QFileDialog, QMessageBox, 
                             QAbstractItemView, QDialog, QLabel, 
                             QFormLayout, QDialogButtonBox, QTableView,
                             QComboBox, QMenu, QTextBrowser, QShortcut, QInputDialog, QDoubleSpinBox, QCheckBox)
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QColor, QIcon, QKeySequence, QBrush
from PyQt5.QtCore import Qt, QAbstractTableModel, QItemSelection, QItemSelectionModel, QPersistentModelIndex, pyqtSignal, QModelIndex
from core import ExperimentLoader, ExperimentManager, Experiment
from pathlib import Path
from gui.functions import open_file_in_system_editor, open_folder_in_explorer
from functions.gui_functions import load_data, load_files, load_folder
from gui.calculate_diameter import AreaDialogBox, AreaDialog
from gui_PtQt.config import icon_path
from experiments.sample import Sample
from gui.small_widgets import BaseDataDialog


class DoubleLayer(BaseDataDialog):
    def __init__(self, items):
        super().__init__()
        
        # 1. Modele i Widoki
        self.source_model = QStandardItemModel()
        self.dest_model = QStandardItemModel()
        
        self.source_view = QTreeView()
        self.dest_view = QTreeView()
        
        for view in [self.source_view, self.dest_view]:
            view.setModel(self.source_model if view == self.source_view else self.dest_model)
            view.setSelectionMode(QAbstractItemView.ExtendedSelection)
            view.setHeaderHidden(False)

        self.source_model.setHorizontalHeaderLabels(['Dostępne Eksperymenty'])
        self.dest_model.setHorizontalHeaderLabels(['Do Analizy'])

        # 2. Przyciski sterujące
        self.btn_add = QPushButton(">")
        self.btn_remove = QPushButton("<")
        self.btn_add_all = QPushButton(">>")
        self.btn_remove_all = QPushButton("<<")
        
        # Layout dla przycisków (pionowy)
        btn_layout = QVBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_add_all)
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_remove)
        btn_layout.addWidget(self.btn_remove_all)
        btn_layout.addStretch()

        # 3. Główny Layout
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.source_view)
        main_layout.addLayout(btn_layout)
        main_layout.addWidget(self.dest_view)
        self.setLayout(main_layout)

        # Połączenia
        self.btn_add.clicked.connect(self.move_selected_to_dest)
        self.btn_remove.clicked.connect(self.move_selected_to_source)
        
        self.populate(items)

    def populate(self, items):
        for index in items:
            experiment = index.data(Qt.UserRole)
            text = index.data(Qt.DisplayRole)
            item = QStandardItem(text)
            item.setData(experiment, Qt.UserRole)
            item.setEditable(False)
            self.source_model.appendRow(item)

    def move_selected_to_dest(self):
        self._move_items(self.source_view, self.source_model, self.dest_model)

    def move_selected_to_source(self):
        self._move_items(self.dest_view, self.dest_model, self.source_model)

    def _move_items(self, view, source_model, dest_model):
        indices = view.selectedIndexes()
        # Sortujemy malejąco po wierszach, aby usuwanie nie psuło indeksów
        indices.sort(key=lambda x: x.row(), reverse=True)
        
        for index in indices:
            # Pobieramy item
            row_data = source_model.takeRow(index.row())
            # Wstawiamy do drugiego modelu
            dest_model.appendRow(row_data)
    