from PyQt5.QtWidgets import QLabel, QTableView, QComboBox, QDialog, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt5.QtCore import QAbstractTableModel, Qt, QModelIndex
import pandas as pd


class PandasModel(QAbstractTableModel):
    def __init__(self, data: pd.DataFrame):
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
                if isinstance(value, float):
                    if value > 1:
                        return f"{value:.2f}"
                    else:
                        return f"{value:.2g}"
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
    
    def insertColumn(self):
        self.beginInsertColumns(QModelIndex(), 0, 0)
        self._data.insert(0, 'New', None)
        self.endInsertColumns()

    def flags(self, index):

        if not index.isValid():
            return Qt.NoItemFlags
        
        item_flags = super().flags(index)
        return item_flags | Qt.ItemIsEditable
    
    def setData(self, index, value, role):

        if not index.isValid():
            return False
        if role == Qt.EditRole:
            cast_value = float(value)
            row, column = index.row(), index.column()
            self._data.iat[row, column] = cast_value

            self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
            return True


class AnalysisViewer(QDialog):
    def __init__(self, object_to_view, parent = None):
        super().__init__(parent)

        self.setWindowTitle('Analysis components')
        self.resize(800, 600)
        self.object_to_view = object_to_view

        main_layout = QVBoxLayout()

        self.add_column_btn = QPushButton('Add Row!')
        self.view = QTableView()
        self.update_table_data(object_to_view)
        main_layout.addWidget(self.add_column_btn)
        main_layout.addWidget(self.view)
        self.setLayout(main_layout)
        self.exec()
    
    def update_table_data(self, object_to_view):
        
        # Sprawdzamy, czy to na pewno DataFrame (currentData może być None przy pustym combo)
        if object_to_view is not None:
            self.flat_object_to_view = object_to_view.reset_index()
            self.model = PandasModel(self.flat_object_to_view)
            self.view.setModel(self.model)
            self.add_column_btn.clicked.connect(self.model.insertColumn)



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