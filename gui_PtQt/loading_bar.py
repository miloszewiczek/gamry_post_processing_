from PyQt5.QtWidgets import (QTreeWidget, QWidget, QLayout, QPushButton, QHBoxLayout, 
                             QVBoxLayout, QTreeView, QFileDialog, QMessageBox, 
                             QAbstractItemView, QDialog, QLabel, 
                             QFormLayout, QDialogButtonBox, QTableView,
                             QComboBox, QMenu, QTextBrowser, QShortcut, QInputDialog, QDoubleSpinBox)
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QColor, QIcon, QKeySequence
from PyQt5.QtCore import Qt, QAbstractTableModel, QItemSelection, QItemSelectionModel, QPersistentModelIndex
from core import ExperimentLoader, ExperimentManager, Experiment
from pathlib import Path
from gui.functions import open_file_in_system_editor, open_folder_in_explorer
from functions.gui_functions import load_data, load_files, load_folder
from gui.calculate_diameter import AreaDialogBox, AreaDialog


class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if index.isValid():
            if role == Qt.ItemDataRole.DisplayRole:
                # Pobieramy wartość z DataFrame
                value = self._data.iloc[index.row(), index.column()]
                return str(value)
        return None

    def headerData(self, section, orientation, role):
        # Ustawienie nazw kolumn i numerów wierszy
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._data.columns[section])
            if orientation == Qt.Orientation.Vertical:
                return str(self._data.index[section])
        return None


class DataPreviewDialog(QDialog):
    def __init__(self, experiment, parent=None):
        super().__init__(parent)

        
        self.setWindowTitle("Podgląd Danych Eksperymentu")
        self.resize(800, 600)
        
        self.experiment = experiment
        self.experiment.load_curves()
        self.experiment.process_data()

        layout = QVBoxLayout(self)
        
        # 1. UI Elements
        self.data_type_combobox = QComboBox()
        self.combobox = QComboBox()
        self.view = QTableView()
        
        layout.addWidget(QLabel("Typ danych:"))
        layout.addWidget(self.data_type_combobox)
        layout.addWidget(QLabel("Wybierz krzywą:"))
        layout.addWidget(self.combobox)
        layout.addWidget(self.view)

        # 2. Logika połączeń (Kaskada)
        # Kiedy zmienia się TYP -> aktualizuj LISTĘ KRZYWYCH
        self.data_type_combobox.currentIndexChanged.connect(self.update_curves_list)
        
        # Kiedy zmienia się KRZYWA -> aktualizuj TABELĘ
        self.combobox.currentIndexChanged.connect(self.update_table_data)

        # 3. Inicjalizacja danych
        data_dict = experiment.get_all_data()

        self.populate_types(data_dict)

    def populate_types(self, data_dict):
        # Blokujemy sygnały, żeby nie wywoływać update_table_data wielokrotnie przy czyszczeniu
        self.data_type_combobox.blockSignals(True)
        self.data_type_combobox.clear()
        
        for type_name, curves_list in data_dict.items():
            self.data_type_combobox.addItem(type_name, curves_list)
        
        self.data_type_combobox.blockSignals(False)
        
        # Ręcznie wywołujemy pierwszą aktualizację
        self.update_curves_list()

    def update_curves_list(self):
        self.combobox.blockSignals(True)
        self.combobox.clear()
        
        curves_list = self.data_type_combobox.currentData()
        if curves_list:
            for i, df in enumerate(curves_list):
                self.combobox.addItem(f"Krzywa {i+1}", df)
        
        self.combobox.blockSignals(False)
        # Po zmianie listy krzywych, odśwież tabelę pierwszą dostępną krzywą
        self.update_table_data()
            
    def update_table_data(self):
        selected_df = self.combobox.currentData()
        
        # Sprawdzamy, czy to na pewno DataFrame (currentData może być None przy pustym combo)
        if selected_df is not None:
            self.model = PandasModel(selected_df)
            self.view.setModel(self.model)

class ExperimentInfoDialog(QDialog):
    def __init__(self, experiment:Experiment, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Info: {experiment.file_name}")
        self.setMinimumWidth(350)
        self.experiment = experiment

        layout = QVBoxLayout(self)
        
        # FormLayout idealnie nadaje się do par "Etykieta: Wartość"
        form = QFormLayout()
        
        self.experiment.load_meta_data()
        for key, val_tuple in experiment.get_essentials().items():
            val = val_tuple[0]
            form.addRow(f"<b>{key}</b>", QLabel(f"{val}"))
        # form.addRow("<b>Nazwa:</b>", QLabel(experiment.file_name))
        # form.addRow("<b>ID:</b>", QLabel(str(experiment.id)))
        # form.addRow("<b>Folder:</b>", QLabel(experiment.folder))
        # form.addRow("<b>Klasa:</b>", QLabel(experiment.__class__.__name__))
        
        layout.addLayout(form)
        
        # Standardowy przycisk OK

        self.btn_change_class = QPushButton("Show Data")
        self.btn_change_class.clicked.connect(self.show_data)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.addButton(self.btn_change_class, QDialogButtonBox.ButtonRole.ActionRole)

        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    def show_data(self):
        data = DataPreviewDialog(self.experiment)
        data.exec()
    
    def open_with(self):
        open_file_in_system_editor(self.experiment.file_path)

class ExperimentPanel(QWidget):
    def __init__(self, loader:ExperimentLoader, manager:ExperimentManager, parent=None, settings = None):
        super().__init__(parent)

        self.loader = loader
        self.manager = manager
        self.settings = settings
        
        # 1. Inicjalizacja Modelu i Widoku
        self.tree_view = QTreeView()
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Experiment', 'Class', 'ID'])
        self.tree_view.setModel(self.model)
        self.tree_view.setColumnWidth(0, 300)
        self.tree_view.setColumnWidth(1, 150)
        self.tree_view.setColumnWidth(2, 10)
        self.tree_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.open_menu)

        # 2. UI - Przyciski
        self.btn_load_dialog = QPushButton()
        self.btn_load_folder_dialog = QPushButton()
        self.btn_delete = QPushButton()
        self.btn_copy = QPushButton()

        self.btn_load_dialog.setShortcut('Ctrl+O')
        self.btn_load_folder_dialog.setShortcut('Ctrl+Shift+O')

        btn_copy_shortcut = QShortcut(QKeySequence("Ctrl+C"), self.tree_view)
        btn_copy_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        btn_copy_shortcut.activated.connect(self.copy_item)

        btn_delete_shortcut = QShortcut(QKeySequence("Delete"), self.tree_view)
        btn_delete_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        btn_delete_shortcut.activated.connect(self.delete_item)  

        btn_select_shortcut = QShortcut(QKeySequence("Ctrl+A"), self.tree_view)
        btn_select_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        btn_select_shortcut.activated.connect(self.select_all)
        self.selected_all = False

        # 2.1 UI - Icons
        self.btn_load_dialog.setIcon(QIcon("Fugue_icons/fugue-icons-3.5.6/icons/document--plus.png"))
        self.btn_load_folder_dialog.setIcon(QIcon("Fugue_icons/fugue-icons-3.5.6/icons/folder-open.png"))
        self.btn_delete.setIcon(QIcon("Fugue_icons/fugue-icons-3.5.6/icons/document--minus.png"))
        self.btn_copy.setIcon(QIcon("Fugue_icons/fugue-icons-3.5.6/icons/document-copy.png"))

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
            exp = index.data(Qt.UserRole)
            dialog = ExperimentInfoDialog(exp, self)
            dialog.exec()

        elif identity == "PARENT":
            print('rodzic')
        else:
            print('nic')
        
    def load_folder(self): 
        files = load_folder(self)
        if files:
            self.load_data(files)

    def load_files(self):
        files = load_files(self)
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
        child_name.setData(exp, Qt.UserRole)
        
        parent_item.appendRow([child_name, child_class, child_id])

    def get_target_indices(self, clicked_index=None):
        """
        Zwraca listę indeksów do przetworzenia.
        Priorytet:
        1. Jeśli kliknięty prawym przyciskiem indeks nie jest w obecnym zaznaczeniu -> tylko ten indeks.
        2. Jeśli kliknięty indeks JEST w zaznaczeniu -> całe zaznaczenie.
        3. Jeśli nie kliknięto w nic konkretnego (np. skrót klawiszowy) -> całe zaznaczenie.
        """
        selection_model = self.tree_view.selectionModel()
        
        # Przypadek: Wywołanie ze skrótu klawiszowego (clicked_index to None lub bool)
        if clicked_index is None or isinstance(clicked_index, bool):
            return selection_model.selectedRows(0)

        # Przypadek: Kliknięcie prawym przyciskiem myszy
        if selection_model.isSelected(clicked_index):
            # Jeśli kliknąłeś w coś, co już jest zaznaczone (część grupy)
            return selection_model.selectedRows(0)
        else:
            # Jeśli kliknąłeś w coś poza zaznaczeniem, traktujemy to jako wybór tylko tego jednego
            return [clicked_index.siblingAtColumn(0)]


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
            experiment = index.data(Qt.UserRole)
            new_experiment = self.manager.copy_experiment(experiment, new_id = self.loader.get_counter())
            self.loader.update_counter(1)
            self.add_experiment_to_model(new_experiment, text = new_experiment.file_name + "_C")
       

    def delete_item(self, index = None):

        # 1. Pobieramy unikalne wiersze (tylko z pierwszej kolumny)
        if (index is None) or (isinstance(index, bool)):
            selected_indices = self.tree_view.selectionModel().selectedRows(0)
        else:
            selected_indices = [index,]
        
        print(selected_indices)

        if not selected_indices:
            QMessageBox.information(self, 'Select node', 'No node selected...')
            return

        # Sortujemy indeksy malejąco (WAŻNE: zapobiega problemom z przesuwaniem się indeksów przy usuwaniu wielu wierszy)
        selected_indices.sort(key=lambda x: x.row(), reverse=True)

        for index in selected_indices:
            tipo = self.identify_selection(index)

            if tipo == "CHILD":
                exp = index.data(Qt.UserRole)
                print(exp)
                parent_index = index.parent()
                # Usuwamy z logiki (manager/baza)
                self.manager.delete_experiment_by_id(exp.id)
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


    def open_menu(self, position):
        index = self.tree_view.indexAt(position)
        if not index.isValid():
            return

        targets = self.tree_view.selectionModel().selectedRows(0)
        # verify if parent and child are in the group
        
        menu_type = self.identify_selection(index)
        menu = self._build_context_menu(menu_type, len(targets))
        action = menu.exec(self.tree_view.viewport().mapToGlobal(position))
        self._handle_experiment_action(action = action, index = targets)

    def _build_context_menu(self, node_type, amount_of_targets):
        
        menu = QMenu()
        
        if node_type == 'CHILD':

            self.action_info = menu.addAction("Show details")

            if amount_of_targets > 1:
                self.action_info.setDisabled(True)

            self.action_notepad = menu.addAction("Open in text editor")
            self.action_change_class = menu.addAction("Change type")
            menu.addSeparator()
            self.action_set_parameters = menu.addAction("Set Geometrical Area")
            self.action_process = menu.addAction("Process")
        
        return menu

    def _handle_experiment_action(self, action, index):
        experiments = self.experimentFromIndex(index)

        if action == getattr(self, 'action_info', None):
            self.on_double_clicked(index[0])

        elif action == getattr(self, 'action_notepad', None):
            for experiment in experiments:
                open_file_in_system_editor(experiment.file_path)

        elif action == getattr(self, 'action_process', None):
            for exp in experiments:
                exp.process_data()
                items = list(map(self.model.itemFromIndex, index))
                for item in items:
                    item.setBackground(QColor('green'))

        elif action == getattr(self, 'action_set_parameters', None):
            x = AreaDialog()        
            if x.exec() == QDialog.Accepted:
                geometric_area = x.get_value()
            else:
                return
            for exp in experiments:
                exp.set_area(geometric_area)

        elif action == getattr(self, 'action_change_class', None):

            x = QDialog()
            layout = QHBoxLayout(x)
            combo = QTreeView()
            model = QStandardItemModel()
            for key, items in self.loader.experiment_classes.items():
                parent = QStandardItem(key)
                print(key)
                model.appendRow(parent)
                for item in items:
                    parent.appendRow(QStandardItem(item))
            
            qbrowser = QTextBrowser()
            qbrowser.setPlaceholderText("Choose experiment to get info")
            qbrowser.setMinimumWidth(200)
            combo.clicked.connect(lambda x: qbrowser.setText(model.item(Qt.DisplayRole)))

            combo.setModel(model)
            layout.addWidget(combo)
            layout.addWidget(qbrowser)
            x.setLayout(layout)
            x.exec()
        
        # elif action == getattr(self, 'explorer_info', None):
        #   open_folder_in_explorer()
        
        else:
            return

    def get_children(self, parent_index):
        children = self.model.rowCount(parent_index)
        indexes = [self.model.index(child, 0, parent_index) for child in range(children)]
        return indexes


    def verify_parent_children_relationship(self, targets):

        parents = [target for target in targets if self.identify_selection(target) == 'PARENT']
        selected_children = [target for target in targets if self.identify_selection(target) == 'CHILD']
        selection_model = self.tree_view.selectionModel()
        selection = QItemSelection()
        
        if (len(parents) != 0) and (len(selected_children) > 0):
            button = QMessageBox.question(self,
                                 "Multiple selection",
                                 "It appears you selected both folder and its child(ren). Extend selection to all children?",
                                 buttons = QMessageBox.StandardButton.Yes
                                 | QMessageBox.StandardButton.No,
                                 defaultButton = QMessageBox.StandardButton.No
                                 )
            if button == QMessageBox.StandardButton.Yes:
                for parent in parents:
                    children = self.get_children(parent)
                    selected_children += children
            elif button == QMessageBox.StandardButton.No:
                selected_children = selected_children

            selected_children = set(selected_children)
            for idx in selected_children:
                selection.select(idx, idx)
            selection_model.select(selection, QItemSelectionModel.SelectionFlag.ClearAndSelect)
        
        return selected_children
                
    def experimentFromIndex(self, indexes) -> list[Experiment]:
        return [index.data(Qt.UserRole) for index in indexes]
        
    def select_all(self):
        pass