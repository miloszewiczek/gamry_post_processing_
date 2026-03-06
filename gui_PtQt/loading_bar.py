from PyQt5.QtWidgets import QTreeWidget, QWidget, QLayout, QPushButton, QHBoxLayout, QVBoxLayout, QTreeView, QFileDialog, QMessageBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt 
from core import ExperimentLoader, ExperimentManager

class ExperimentTree(QTreeWidget):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.setHeaderLabels(['Name', 'ID', 'Type'])
        self.setMinimumHeight(20)


class ExperimentPanel(QWidget):
    def __init__(self, loader:ExperimentLoader, manager:ExperimentManager, parent=None):
        super().__init__(parent)
        self.loader = loader
        self.manager = manager
        
        # 1. Inicjalizacja Modelu i Widoku
        self.tree_view = QTreeView()
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['ID', 'File Name'])
        self.tree_view.setModel(self.model)
        
        # 2. UI - Przyciski
        self.btn_load = QPushButton("Załaduj pliki testowe (input/)")
        self.btn_clear = QPushButton("Wyczyść listę")
        self.btn_load_dialog = QPushButton("Wybierz pliki")
        self.btn_delete = QPushButton('Usuń węzeł')
        self.btn_copy = QPushButton("Skopiuj")

        # 3. Layouty
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.btn_load)
        button_layout.addWidget(self.btn_clear)
        button_layout.addWidget(self.btn_load_dialog)
        button_layout.addWidget(self.btn_delete)
        button_layout.addWidget(self.btn_copy)
        
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.tree_view)
        
        # 4. Połączenia Sygnałów
        self.btn_load.clicked.connect(self.handle_load_data)
        self.btn_clear.clicked.connect(self.clear_list)
        self.btn_load_dialog.clicked.connect(self.load_data)
        self.btn_delete.clicked.connect(self.delete_item)
        self.btn_copy.clicked.connect(self.copy_item)

    def load_data(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Choose files",
            "",
            "Gamry files (*.DTA);;All files (*)"
        )
        if files:
            for file in files:
                try:
                    # providing manager in create_experiment automatically updates the manager's dict_of_experiments
                    experiment = self.loader.create_experiment(file)
                    self.manager.add_experiment(experiment)
                    
                except Exception as e:
                    pass
                
            self.populate_tree()

    def populate_tree(self):

        self.model.clear()

        grouped = {}
        for exp in self.manager.get_all():
            grouped.setdefault(exp.folder, []).append(exp)

        for path, exps in grouped.items():
            parent = QStandardItem(path)
            self.model.appendRow(parent)
            for exp in exps:
                child = QStandardItem(exp.file_name)
                child.setData(exp.id, Qt.UserRole)
                parent.appendRow(child)

    def identify_selection(self, index):
        if not index.isValid():
            return "Nic"
        
        if not index.parent().isValid():
            return "PARENT"
        else:
            return "CHILD"
        
    def copy_item(self):
        selected_indices = self.tree_view.selectedIndexes()
        indices = [i for i in selected_indices if i.column() == 0]
        
        for index in indices:
            index_data = index.data(Qt.UserRole)
            self.manager.copy_experiment(index_data)
        self.populate_tree()

    def delete_item(self):
        selected_indices = self.tree_view.selectedIndexes()
        indices = [i for i in selected_indices if i.column() == 0]
        if len(indices) == 0:
            QMessageBox.information(
                self,
                'Select node',
                'No node selected. Left click on a node, and try again',
                QMessageBox.Ok,
                QMessageBox.Ok
            )

        for index in indices:
            tipo = self.identify_selection(index)

            if tipo == "CHILD":
                exp_id = index.data(Qt.UserRole)
                self.manager.remove(exp_id)
            elif tipo == "PARENT":
                path_name = index.data(Qt.DisplayRole)
                reply = QMessageBox.question(
                    self,
                    'Deleting Folder',
                    'You are about to delete all experiments from this folder. Proceed?',
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    self.manager.delete_by_path(path_name)
                    print('Deleting all')
                else:
                    print("Nothing's changed...")
        
        self.populate_tree()

                

    def handle_load_data(self):
        """Metoda pełniąca rolę mostu"""
        # A. Wywołujemy logikę z managera (tę naprawioną wcześniej)
        experiments = self.manager.get_all()
        
        # B. Odświeżamy widok w GUI
        self.update_tree_from_manager(experiments)

    def update_tree_from_manager(self, experiments):
        """Przepisuje listę obiektów Experiment na wiersze w QStandardItemModel"""
        self.model.removeRows(0, self.model.rowCount()) # Czyścimy stare dane w modelu
        
        for exp in experiments:
            # Tworzymy wiersz danych
            name_item = QStandardItem(str(exp.id)) # Zakładając, że Experiment ma .name
            path_item = QStandardItem(exp.file_name) # Zakładając .file_path
            
            # Opcjonalnie: chowamy ID w UserRole dla późniejszego wyboru
            name_item.setData(exp.id, Qt.UserRole)
            
            # Dodajemy wiersz do modelu
            self.model.appendRow([name_item, path_item])
            
        print(f"Zaktualizowano GUI: dodano {len(experiments)} elementów.")

    def clear_list(self):
        self.model.clear()
        self.model.setHorizontalHeaderLabels(['Nazwa Eksperymentu', 'Ścieżka pliku'])
        # Tutaj opcjonalnie: self.manager.reset_experiments()