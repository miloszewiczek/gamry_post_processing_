from PyQt5.QtWidgets import QTreeWidget, QWidget, QLayout, QPushButton, QHBoxLayout, QVBoxLayout, QTreeView, QFileDialog, QMessageBox, QAbstractItemView, QDialog, QLabel, QFormLayout, QDialogButtonBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt 
from core import ExperimentLoader, ExperimentManager

from pathlib import Path

class ExperimentInfoDialog(QDialog):
    def __init__(self, experiment, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Info: {experiment.file_name}")
        self.setMinimumWidth(350)
        
        layout = QVBoxLayout(self)
        
        # FormLayout idealnie nadaje się do par "Etykieta: Wartość"
        form = QFormLayout()
        form.addRow("<b>Nazwa:</b>", QLabel(experiment.file_name))
        form.addRow("<b>ID:</b>", QLabel(str(experiment.id)))
        form.addRow("<b>Folder:</b>", QLabel(experiment.folder))
        form.addRow("<b>Klasa:</b>", QLabel(experiment.__class__.__name__))
        
        layout.addLayout(form)
        
        # Standardowy przycisk OK
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

class ExperimentPanel(QWidget):
    def __init__(self, loader:ExperimentLoader, manager:ExperimentManager, parent=None):
        super().__init__(parent)

        self.loader = loader
        self.manager = manager
        
        # 1. Inicjalizacja Modelu i Widoku
        self.tree_view = QTreeView()
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Experiment', 'Class'])
        self.tree_view.setModel(self.model)
        self.tree_view.setColumnWidth(0, 250)
        self.tree_view.setColumnWidth(1, 100)
        self.tree_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        
        # 2. UI - Przyciski
        self.btn_load_dialog = QPushButton("Wybierz pliki")
        self.btn_load_folder_dialog = QPushButton("Wybierz folder")
        self.btn_delete = QPushButton('Usuń węzeł')
        self.btn_copy = QPushButton("Skopiuj")
        

        # 3. Layouty
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.btn_load_folder_dialog)
        button_layout.addWidget(self.btn_load_dialog)
        button_layout.addWidget(self.btn_delete)
        button_layout.addWidget(self.btn_copy)
        
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.tree_view)
        
        # 4. Połączenia Sygnałów
        self.btn_load_dialog.clicked.connect(self.load_files)
        self.btn_load_folder_dialog.clicked.connect(self.load_folder)
        self.btn_delete.clicked.connect(self.delete_item)
        self.btn_copy.clicked.connect(self.copy_item)

        self.tree_view.doubleClicked.connect(self.on_double_clicked)

    def on_double_clicked(self, index):
        
        if index.column() != 0:
            index = index.siblingAtColumn(0)

        identity = self.identify_selection(index)
        if identity == "CHILD":
            exp = self.manager.get(index.data(Qt.UserRole))
            dialog = ExperimentInfoDialog(exp, self)
            dialog.exec()

        elif identity == "PARENT":
            print('rodzic')
        else:
            print('nic')
        
    def load_folder(self): 
        folder = QFileDialog.getExistingDirectory(
            self,
            "Choose Folder",
            ""
        )
        normalized_folder_path = Path(folder)
        files = normalized_folder_path.glob('*.DTA')
        if files:
            self.load_data(files)

    def load_files(self):

        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Choose files",
            "",
            "Gamry files (*.DTA);;All files (*)"
        )
        if files:
            self.load_data(files)

    def load_data(self, files):

        for file in files:
            try:
                # providing manager in create_experiment automatically updates the manager's dict_of_experiments
                experiment = self.loader.create_experiment(str(file))
                self.manager.add_experiment(experiment)
                self.add_experiment_to_model(experiment)

            except Exception as e:
                pass
                

    def add_experiment_to_model(self, exp, text = None):
        # 1. Sprawdź, czy folder (rodzic) już istnieje w modelu
        parent_item = None
        for row in range(self.model.rowCount()):
            item = self.model.item(row)
            if item.text() == exp.folder:
                parent_item = item
                break
        
        # 2. Jeśli nie ma takiego folderu, stwórz go
        if not parent_item:
            parent_item = QStandardItem(exp.folder)
            self.model.appendRow(parent_item)
        
        # 3. Dodaj wiersz z danymi eksperymentu
        if text is None:
            child_name = QStandardItem(exp.file_name)
        else:
            child_name = QStandardItem(text)

        child_id = QStandardItem(str(exp.id))
        child_class = QStandardItem(exp.__class__.__name__)
        
        # Pamiętaj o UserRole dla ID, żeby usuwanie działało!
        child_name.setData(exp.id, Qt.UserRole)
        
        parent_item.appendRow([child_name, child_id, child_class])


    def identify_selection(self, index):
        if not index.isValid():
            return "Nic"
        
        if not index.parent().isValid():
            return "PARENT"
        else:
            return "CHILD"
        
    def copy_item(self):

        selected_indices = self.tree_view.selectionModel().selectedRows(0)
        
        for index in selected_indices:
            index_data = index.data(Qt.UserRole)
            new_experiment = self.manager.copy_experiment(index_data, new_id = self.loader.get_counter())
            self.loader.update_counter(1)
            self.add_experiment_to_model(new_experiment, text = new_experiment.file_name + "_C")
       

    def delete_item(self):
        # 1. Pobieramy unikalne wiersze (tylko z pierwszej kolumny)
        selected_indices = self.tree_view.selectionModel().selectedRows(0)
        
        if not selected_indices:
            QMessageBox.information(self, 'Select node', 'No node selected...')
            return

        # Sortujemy indeksy malejąco (WAŻNE: zapobiega problemom z przesuwaniem się indeksów przy usuwaniu wielu wierszy)
        selected_indices.sort(key=lambda x: x.row(), reverse=True)

        for index in selected_indices:
            tipo = self.identify_selection(index)

            if tipo == "CHILD":
                exp_id = index.data(Qt.UserRole)
                parent_index = index.parent()
                # Usuwamy z logiki (manager/baza)
                self.manager.delete_experiment_by_id(exp_id)
                # Usuwamy bezpośrednio z modelu (bez odświeżania całego drzewa)
                self.model.removeRow(index.row(), index.parent())
                
                if self.model.rowCount(parent_index) == 0:
                    self.model.removeRow(parent_index.row(), parent_index.parent())

            elif tipo == "PARENT":
                path_name = index.data(Qt.DisplayRole)
                reply = QMessageBox.question(self, 'Deleting Folder', 
                                        'Delete all experiments?', 
                                        QMessageBox.Yes | QMessageBox.No)
                
                if reply == QMessageBox.Yes:
                    self.manager.delete_by_path(path_name)
                    # Usuwamy cały folder z widoku
                    self.model.removeRow(index.row(), index.parent())
