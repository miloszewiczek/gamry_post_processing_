from PyQt5.QtWidgets import (QDoubleSpinBox, QDialog, QSpinBox, QComboBox, 
QLineEdit, QCheckBox, QTreeView, QHBoxLayout, QVBoxLayout, QPushButton, QAbstractItemView, QListView, QDialogButtonBox)
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import QSettings, Qt, QAbstractTableModel, QItemSelection, QItemSelectionModel, QPersistentModelIndex, pyqtSignal, QModelIndex, QSortFilterProxyModel
import json
from experiments.base import Experiment
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTreeView, QLabel, QAbstractItemView
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, pyqtSignal
from experiments.sample import Sample

class SimpleDoubleSpinBox(QDoubleSpinBox):
    def __init__(self, value, range:tuple = None, minimum = 0, maximum = 100000):
        super().__init__()
        self.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        self.setDecimals(3)
        self.setMinimum(minimum)
        self.setMaximum(maximum)
        self.setValue(value)
        if range:
            self.setRange(range[0], range[1])
    
    def setValue(self, value):
        try:
            float_value = float(value)
            super().setValue(float_value)
        except:
            raise TypeError


class BaseDataDialog(QDialog):
    def __init__(self, parent=None, settings_key = None):
        super().__init__(parent)
        self.fields = {}
        # Klucz, pod którym okno będzie pamiętać swoje ustawienia w QSettings
        self.settings_key = settings_key

    def get_data(self):
        """
        Automatically collect data from widgets present in self.fields.
        """
        data = {}
        for key, widget in self.fields.items():
            if isinstance(widget, QDoubleSpinBox) or isinstance(widget, QSpinBox):
                data[key] = widget.value()
            elif isinstance(widget, QComboBox):
                # Zwracamy currentData (jeśli przechowujesz tam np. tuple z potencjałami)
                # Jeśli danych nie ma, fallback do currentText()
                val = widget.currentData()
                data[key] = val if val is not None else widget.currentText()
            elif isinstance(widget, QCheckBox):
                data[key] = widget.isChecked()
            elif isinstance(widget, QLineEdit):
                data[key] = widget.text()

            else:
                # Opcjonalnie: obsługa własnych atrybutów, jeśli widget ma metodę 'get_value'
                if hasattr(widget, 'get_value'):
                    data[key] = widget.get_value()
        return data

    def set_data(self, data):
        """Automatycznie rozsyła dane do odpowiednich widgetów."""
        if not data:
            return

        self.blockSignals(True)
        for key, value in data.items():
            widget = self.fields.get(key)
            if not widget:
                continue

            if isinstance(widget, (QDoubleSpinBox, QSpinBox)):
                widget.setValue(float(value))
            elif isinstance(widget, QCheckBox):
                widget.setChecked(bool(value))
            elif isinstance(widget, QLineEdit):
                widget.setText(str(value))
            elif isinstance(widget, QComboBox):
                # Próbujemy ustawić po tekście (najbezpieczniejsze dla profili JSON)
                index = widget.findText(str(value))
                if index >= 0:
                    widget.setCurrentIndex(index)
                # Jeśli value to int (index), ustawiamy po indeksie
                elif isinstance(value, int):
                    widget.setCurrentIndex(value)
        self.blockSignals(False)


    def load_from_settings(self):
        """Ładuje ostatnie wartości z QSettings."""
        if not self.settings_key:
            return
            
        settings = QSettings()
        raw_data = settings.value(f"cache/{self.settings_key}")
        if raw_data:
            try:
                self.set_data(json.loads(raw_data))
            except Exception as e:
                print(f"Błąd ładowania cache: {e}")

    def save_to_settings(self):
        """Zapisuje aktualne wartości do QSettings."""
        if not self.settings_key:
            return
            
        settings = QSettings()
        data = self.get_data()
        settings.setValue(f"cache/{self.settings_key}", json.dumps(data))


class Selector(BaseDataDialog):

    item_changed = pyqtSignal(dict)

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
        self.item_changed.emit()

    def move_selected_to_source(self):
        self._move_items(self.dest_view, self.dest_model, self.source_model)
        self.item_changed.emit()

    def get_experiments_to_analysis(self) -> list[Experiment]:
        experiments = []
        model = self.dest_model
        for row in range(model.rowCount()):
            item = model.item(row, 0)
            if item:
                exp = item.data(Qt.UserRole)
                experiments.append(exp)
        return {"All experiments": experiments}

    def _move_items(self, view, source_model, dest_model):
        print('Pronto!')
        indices = view.selectedIndexes()
        # Sortujemy malejąco po wierszach, aby usuwanie nie psuło indeksów
        indices.sort(key=lambda x: x.row(), reverse=True)
        
        for index in indices:
            # Pobieramy item
            row_data = source_model.takeRow(index.row())
            # Wstawiamy do drugiego modelu
            dest_model.appendRow(row_data)

class ExperimentFilterProxy(QSortFilterProxyModel):
    """Prosty filtr, który decybuje, co wyświetlić w danym oknie"""
    def __init__(self, show_selected: bool):
        super().__init__()
        self.show_selected = show_selected

    def filterAcceptsRow(self, source_row, source_parent):
        model = self.sourceModel()
        # Pobieramy indeks dla sprawdzanego wiersza
        index = model.index(source_row, 0, source_parent)
        
        # Jeśli to jest Sample (węzeł główny), zawsze go pokazujemy, 
        # Qt samo ukryje go, jeśli nie będzie miał żadnych dzieci.
        if not source_parent.isValid():
            return True
            
        # Jeśli to Experiment, sprawdzamy flagę "selected" (domyślnie False)
        is_selected = bool(index.data(Qt.ItemDataRole.UserRole + 1))
        
        # Zwracamy True tylko, jeśli stan dopasowania się zgadza
        return is_selected == self.show_selected


class SelectorWithSample(Selector):

    flat_list_signal = pyqtSignal(list)

    def __init__(self, items):
        # Inicjalizujemy bazę, ale zaraz podmienimy modele widoków na proxy
        super().__init__(items)
        
        # Tworzymy dwa filtry podpięte pod ten sam model źródłowy (source_model)
        self.left_proxy = ExperimentFilterProxy(show_selected=False)
        self.left_proxy.setSourceModel(self.source_model)
        
        self.right_proxy = ExperimentFilterProxy(show_selected=True)
        self.right_proxy.setSourceModel(self.source_model)
        
        # Przepinamy widoki na nasze filtry
        self.source_view.setModel(self.left_proxy)
        self.dest_view.setModel(self.right_proxy)
        
        # Rozwijamy drzewa, żeby od razu wszystko było widać
        self.source_view.expandAll()
        self.dest_view.expandAll()

        self.btn_add_all.clicked.connect(self._move_all_to_right)
        self.btn_remove_all.clicked.connect(self._move_all_to_left)

    def populate(self, items: dict[Sample, list[Experiment]]):
        """Pierwotna, płaska struktura: Sample -> list[Experiment]"""
        self.source_model.clear()
        self.source_model.setHorizontalHeaderLabels(['Eksperymenty'])
        
        for sample, experiments in items.items():
            sample_item = QStandardItem(sample.sample_name)
            sample_item.setData(sample, Qt.ItemDataRole.UserRole)
            
            for experiment in experiments:
                exp_item = QStandardItem(experiment.file_name)
                exp_item.setData(experiment, Qt.ItemDataRole.UserRole)
                # Dodatkowa flaga: False = do wyboru (lewo), True = wybrane (prawo)
                exp_item.setData(False, Qt.ItemDataRole.UserRole + 1)
                sample_item.appendRow(exp_item)
                
            self.source_model.appendRow(sample_item)
            
        self.source_view.expandAll()
        self.dest_view.expandAll()

    def _toggle_selection(self, view, proxy_model, target_state: bool):
        """Oryginalna, stabilna wersja dla drzewa dwupoziomowego"""
        proxy_indices = view.selectedIndexes()
        source_items = []
        
        for proxy_idx in proxy_indices:
            if proxy_idx.column() == 0:  # Zabezpieczenie przed wieloma kolumnami
                source_idx = proxy_model.mapToSource(proxy_idx)
                
                # Sprawdzamy czy to Experiment (ma rodzica)
                if source_idx.parent().isValid():
                    item = self.source_model.itemFromIndex(source_idx)
                    if item and item not in source_items:
                        source_items.append(item)
                else:
                    # Jeśli kliknięto w węzeł główny (Sample), zaznaczamy wszystkie jego dzieci
                    parent_item = self.source_model.itemFromIndex(source_idx)
                    if parent_item:
                        for row in range(parent_item.rowCount()):
                            child_item = parent_item.child(row, 0)
                            if child_item and child_item not in source_items:
                                source_items.append(child_item)

        # Zmieniamy stan TYLKO na przygotowanej, stabilnej liście obiektów
        for item in source_items:
            item.setData(target_state, Qt.ItemDataRole.UserRole + 1)
                
        # Odświeżamy widoki przez proxy
        self.left_proxy.invalidateFilter()
        self.right_proxy.invalidateFilter()
        
        self.source_view.expandAll()
        self.dest_view.expandAll()

    def _move_all_to_right(self):
        self.source_view.selectAll()
        self._toggle_selection(self.source_view, self.left_proxy, target_state=True)
        self.flat_list_signal.emit(self.get_flat())

    def _move_all_to_left(self):
        self.dest_view.selectAll()
        self._toggle_selection(self.dest_view, self.right_proxy, target_state=False)
        self.flat_list_signal.emit(self.get_flat())


    def move_selected_to_dest(self):
        self._toggle_selection(self.source_view, self.left_proxy, target_state=True)
        self.flat_list_signal.emit(self.get_flat())

    def move_selected_to_source(self):
        self._toggle_selection(self.dest_view, self.right_proxy, target_state=False)
        self.flat_list_signal.emit(self.get_flat())


    def get_flat(self):
        result = []
        for row in range(self.source_model.rowCount()):
            sample_item = self.source_model.item(row, 0)
            sample_obj = sample_item.data(Qt.UserRole)

            if sample_item:
                for child_row in range(sample_item.rowCount()):
                    exp_item = sample_item.child(child_row, 0)
                    if exp_item and exp_item.data(Qt.ItemDataRole.UserRole + 1) == True:
                        exp_obj = exp_item.data(Qt.ItemDataRole.UserRole)
                        
                        result.append(exp_obj)

        return result

    def get_experiments_to_analysis(self) -> dict[Sample, list[Experiment]]:
        """Zwraca czystą, płaską strukturę wybranych plików"""
        from collections import defaultdict
        experiments_dict = defaultdict(list)

        for row in range(self.source_model.rowCount()):
            sample_item = self.source_model.item(row, 0)
            sample_obj = sample_item.data(Qt.UserRole)

            if sample_item:
                for child_row in range(sample_item.rowCount()):
                    exp_item = sample_item.child(child_row, 0)
                    if exp_item and exp_item.data(Qt.ItemDataRole.UserRole + 1) == True:
                        exp_obj = exp_item.data(Qt.ItemDataRole.UserRole)
                        experiments_dict[sample_obj].append(exp_obj)
        
        return dict(experiments_dict)
    
    def get_flat_list(self):
        experiments_list = []

        for row in range(self.source_model.rowCount()):
            sample_item = self.source_model.item(row, 0)

            if sample_item:
                for child_row in range(sample_item.rowCount()):
                    exp_item = sample_item.child(child_row, 0)
                    if exp_item and exp_item.data(Qt.ItemDataRole.UserRole + 1) == True:
                        exp_obj = exp_item.data(Qt.ItemDataRole.UserRole)
                        experiments_list.append(exp_obj)
        
        return experiments_list
    

class TreeSelectorWithCheckboxes(QWidget):
    # Sygnał wysyłany do okna z wykresem, gdy zmieni się stan jakiegokolwiek checkboxa
    item_changed = pyqtSignal()

    def __init__(self, main_model, selected_indices):
        super().__init__()
        self.main_model = main_model

        # 1. Tworzymy widok drzewiasty podpięty pod TWÓJ ORYGINALNY MODEL aplikacji
        # Dzięki temu nie duplikujemy danych i nie marnujemy pamięci RAM
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.main_model)
        self.tree_view.setSelectionMode(QAbstractItemView.NoSelection) # Interakcja wyłącznie przez checkboxy
        
        # Dopasowanie kolumn do Twojego układu (Experiment | Class | ID)
        self.tree_view.setColumnWidth(0, 260)
        self.tree_view.setColumnWidth(1, 100)
        self.tree_view.setColumnWidth(2, 40)

        # 2. Układ interfejsu (Minimalistyczny i przejrzysty)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>Wybierz eksperymenty do analizy:</b>"))
        layout.addWidget(self.tree_view)

        # 3. Aktywacja checkboxów i przeniesienie zaznaczenia startowego
        self._initialize_checkboxes(selected_indices)

        # 4. Łączymy sygnał zmiany elementu z naszą logiką automatyki zaznaczania
        self.main_model.itemChanged.connect(self.on_checkbox_state_changed)

    def _initialize_checkboxes(self, selected_indices):
        """Włącza funkcję checkboxów w całym modelu i zaznacza te, 

        które użytkownik miał podświetlone na ekranie głównym."""
        # Blokujemy sygnały modelu, żeby kaskada nie odpalała się podczas konfiguracji startowej
        self.main_model.blockSignals(True)

        # Krok A: Przechodzimy przez całe drzewo i dodajemy puste checkboxy (Unchecked)
        for row in range(self.main_model.rowCount()):
            parent_item = self.main_model.item(row, 0)
            if parent_item:
                parent_item.setCheckable(True)
                parent_item.setCheckState(Qt.Unchecked)
                
                for child_row in range(parent_item.rowCount()):
                    child_item = parent_item.child(child_row, 0)
                    if child_item:
                        child_item.setCheckable(True)
                        child_item.setCheckState(Qt.Unchecked)

        # Krok B: Przekładamy zaznaczenie (podświetlenie) z głównego okna na ptaszki
        for idx in selected_indices:
            item = self.main_model.itemFromIndex(idx)
            if not item:
                continue
                
            # Jeśli kliknięto w kolumnę inną niż pierwsza, bierzemy sąsiada z kolumny 0
            if item.column() != 0:
                item = item.parent().child(item.row(), 0) if item.parent() else self.main_model.item(item.row(), 0)

            item.setCheckState(Qt.Checked)
            
            # AUTOMATYKA STARTOWA: Jeśli zaznaczono cały folder Sample, zaznacz też dzieci
            if item.hasChildren():
                for r in range(item.rowCount()):
                    item.child(r, 0).setCheckState(Qt.Checked)

        self.main_model.blockSignals(False)
        self.tree_view.expandAll()

    def on_checkbox_state_changed(self, item):
        """Główny menedżer automatyki zaznaczania w dół i w górę."""
        # Blokujemy sygnały, aby uniknąć pętli zwrotnej (zmiana dziecka zmienia rodzica, 
        # a zmiana rodzica zmienia dziecko...)
        self.main_model.blockSignals(True)

        identity = item.data(Qt.UserRole)

        # =====================================================================
        # SPECYFICZNA LOGIKA DLA SAMPLE (Kliknięcie w folder-rodzica)
        # =====================================================================
        if isinstance(identity, Sample) and item.hasChildren():
            # Pobieramy stan, jaki użytkownik kliknął na folderze (Checked lub Unchecked)
            new_folder_state = item.checkState()
            
            # Wymuszamy ten sam stan na wszystkich dzieciach wewnątrz tego folderu
            for r in range(item.rowCount()):
                child = item.child(r, 0)
                if child:
                    child.setCheckState(new_folder_state)

        # =====================================================================
        # LOGIKA DLA EKSPEROMENTU (Kliknięcie w pojedyncze dziecko)
        # =====================================================================
        elif isinstance(identity, Experiment) and item.parent():
            parent_item = item.parent()
            
            # Zbieramy obecne stany wszystkich dzieci z tej gałęzi
            child_states = [parent_item.child(r, 0).checkState() for r in range(parent_item.rowCount())]
            
            # Jeśli wszystkie pliki są zaznaczone -> zaznacz folder
            if all(state == Qt.Checked for state in child_states):
                parent_item.setCheckState(Qt.Checked)
            # Jeśli wszystkie pliki są czyste -> odznacz folder
            elif all(state == Qt.Unchecked for state in child_states):
                parent_item.setCheckState(Qt.Unchecked)
            # Jeśli część jest zaznaczona, a część nie -> ustaw kwadracik częściowego zaznaczenia
            else:
                parent_item.setCheckState(Qt.PartiallyChecked)

        self.main_model.blockSignals(False)
        
        # Wysyłamy sygnał na zewnątrz (wykres natychmiast wie, że trzeba się przerysować!)
        self.item_changed.emit()

    def get_experiments_to_analysis(self) -> list[Experiment]:
        """Przeszukuje model i zwraca gotową płaską listę obiektów Experiment, 

        które posiadają zaznaczony checkbox (Checked)."""
        selected_experiments = []
        
        for row in range(self.main_model.rowCount()):
            parent_item = self.main_model.item(row, 0)
            if parent_item:
                for child_row in range(parent_item.rowCount()):
                    child_item = parent_item.child(child_row, 0)
                    # Sprawdzamy tylko te pliki, które mają pełny stan Checked (ptaszek)
                    if child_item and child_item.checkState() == Qt.Checked:
                        exp = child_item.data(Qt.UserRole)
                        if isinstance(exp, Experiment):
                            selected_experiments.append(exp)
                            
        return selected_experiments


    
    

class TreeFilterProxyModel(QSortFilterProxyModel):
    """
    Własny proxy model, który dba o to, aby dzieci pasujących elementów 
    oraz rodzice pasujących elementów byli widoczni.
        """
    def __init__(self, parent=None):
        super().__init__(parent)
        # Ignorujemy wielkość liter przy wyszukiwaniu
        self.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

    def filterAcceptsRow(self, source_row, source_parent):
        # Jeśli domyślny filtr akceptuje ten wiersz, to super
        if super().filterAcceptsRow(source_row, source_parent):
            return True

        # Jeśli sam wiersz nie pasuje, sprawdzamy czy któreś z jego dzieci pasuje
        source_model = self.sourceModel()
        source_index = source_model.index(source_row, 0, source_parent)
        
        if source_model.hasChildren(source_index):
            for i in range(source_model.rowCount(source_index)):
                if self.filterAcceptsRow(i, source_index):
                    return True
                    
        return False


class ExperimentSelector(QWidget):
    # Poprawna definicja sygnału
    selection_changed = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Inicjalizujemy czyste UI
        self.sample_combobox = QComboBox()
        self.listview = QListView()
        self.listview_model = QStandardItemModel()
        self.listview.setModel(self.listview_model)
        
        self.sample_experiment_dict = {}  # Bezpieczny fallback na pusty słownik
        
        self.build_ui()
        
        # Łączymy sygnały UI
        self.sample_combobox.currentIndexChanged.connect(self.populate_sample)
        
        # POPRAWKA: Podpinamy się pod selectionModel bezpośrednio z listview
        self.listview.selectionModel().currentChanged.connect(self.on_selection_changed)

    def build_ui(self):
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.sample_combobox)
        main_layout.addWidget(self.listview)
        self.setLayout(main_layout)

    def populate_sample(self, index):
        self.listview_model.clear()
        if index < 0:
            return

        sample_key = self.sample_combobox.itemData(index)
        experiments = self.sample_experiment_dict.get(sample_key, [])

        for experiment in experiments:
            exp_item = QStandardItem(experiment.file_name)
            exp_item.setData(experiment, Qt.UserRole)
            self.listview_model.appendRow(exp_item)

        # POPRAWKA: Usunięto problematyczne i niepotrzebne self.listview.currentChanged()

    def on_selection_changed(self, current_index, previous_index):
        if not current_index.isValid():
            return

        # Wyciągamy ukryty obiekt eksperymentu
        selected_experiment = self.listview_model.data(current_index, Qt.UserRole)        
        
        # POPRAWKA: Użycie właściwej nazwy sygnału (selection_changed zamiast experiment_selected)
        self.selection_changed.emit(selected_experiment) 

    def set_experiments(self, manager, experiments=None, samples=None, 
                        sample_experiment_dict=None, name=None, cycle=None, object_type=None):
        """Metoda dedykowana wyłącznie do ładowania i filtrowania danych"""
        self.manager = manager
        
        if sample_experiment_dict:
            sample_objects = sample_experiment_dict.keys()
        elif experiments:
            sample_objects = self.manager.construct_tree(experiments)
        elif samples:
            sample_objects = samples
        else:
            sample_objects = []

        sample_filtered = self.manager.filter_samples(
            samples=sample_objects, name=name, cycle=cycle, object_type=object_type
        )
        self.sample_experiment_dict = sample_filtered

        # Populacja comboboxa
        self.sample_combobox.blockSignals(True)
        self.sample_combobox.clear()
        for sample_key in sample_filtered.keys():
            self.sample_combobox.addItem(sample_key.sample_name, sample_key)
        self.sample_combobox.blockSignals(False)

        # Załaduj pierwszą paczkę danych jeśli combobox nie jest pusty
        if self.sample_combobox.count() > 0:
            self.sample_combobox.setCurrentIndex(0)
            self.populate_sample(0)


class DataSelector(QDialog):
    myaccepted = pyqtSignal(tuple)

    def __init__(self, canvas_type = None, parent=None):
        super().__init__(parent)
        from gui_PtQt.plotting_area import PlottingCanvas

        self.canvas = self.setup_canvas(PlottingCanvas)
        self.toolbar = self.canvas.get_toolbar()        
        # POPRAWKA: Przekazanie self jako parent
        self.experiment_selector = ExperimentSelector(self)
        self.experiment_selector.selection_changed.connect(lambda exp: self.canvas.plot_experiments_no_color(exp, None, marker = 'o', markersize = 2, linewidth = 0))

        self.build_ui()

    def build_ui(self):
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.experiment_selector)

        canvas_layout = QVBoxLayout()
        canvas_layout.addWidget(self.canvas)

        if self.toolbar:
            canvas_layout.addWidget(self.toolbar)
        main_layout.addLayout(canvas_layout)

        buttons = QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        self.button_box = QDialogButtonBox(buttons)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

    def setup_data(self, *args, **kwargs):
        """
        Kwargs inlcude:
            manager: ExperimentManager

            Structured data (choose one):
                -experiments: list of Experiment
                -samples: list of Sample
                -sample_experiment_dict: dictionary in the form: Sample: list[Experiment]

            Filtering options (based on ExperimentManager options):
                -name (str): file_name
                -cycle (int): cycle number
                -object_type (Object): object to filter out. Could be for example EIS or CyclicVoltammetry
            """
        self.experiment_selector.set_experiments(*args, **kwargs)

    def setup_canvas(self, canvas_type):
        return canvas_type(toolbar = True)
    
    def accept(self):
        self.myaccepted.emit(self.canvas.get_selected_point()) # returns x and y coordinates of a point
        super().accept()