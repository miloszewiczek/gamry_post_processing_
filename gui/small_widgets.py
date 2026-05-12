from PyQt5.QtWidgets import QDoubleSpinBox, QDialog, QSpinBox, QComboBox, QLineEdit, QCheckBox, QTreeView, QHBoxLayout, QVBoxLayout, QPushButton, QAbstractItemView
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import QSettings, Qt, QAbstractTableModel, QItemSelection, QItemSelectionModel, QPersistentModelIndex, pyqtSignal, QModelIndex
import json
from experiments.base import Experiment

class SimpleDoubleSpinBox(QDoubleSpinBox):
    def __init__(self, value, range:tuple = None):
        super().__init__()
        self.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        self.setDecimals(3)
        self.setValue(value)
        if range:
            self.setRange(range[0], range[1])


class BaseDataDialog(QDialog):
    def __init__(self, parent=None, settings_key = None):
        super().__init__(parent)
        self.fields = {}
        # Klucz, pod którym okno będzie pamiętać swoje ustawienia w QSettings
        self.settings_key = settings_key

    def get_data(self):
        """Automatycznie zbiera dane z widgetów zarejestrowanych w self.fields."""
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

    item_changed = pyqtSignal()

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
        return experiments

    def _move_items(self, view, source_model, dest_model):
        indices = view.selectedIndexes()
        # Sortujemy malejąco po wierszach, aby usuwanie nie psuło indeksów
        indices.sort(key=lambda x: x.row(), reverse=True)
        
        for index in indices:
            # Pobieramy item
            row_data = source_model.takeRow(index.row())
            # Wstawiamy do drugiego modelu
            dest_model.appendRow(row_data)