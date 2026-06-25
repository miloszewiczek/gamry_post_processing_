import xml.etree.ElementTree as ET
from PyQt5.QtWidgets import (QTreeView, QTextEdit, QHBoxLayout, QSplitter, QWidget, 
                             QMainWindow, QApplication, QDialog, QComboBox, QLabel, 
                             QDialogButtonBox, QVBoxLayout, QGridLayout, QFileDialog)
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QColor, QIcon, QKeySequence, QBrush
from PyQt5.QtCore import Qt, QAbstractTableModel, QItemSelection, QItemSelectionModel, QPersistentModelIndex, pyqtSignal, QModelIndex
from sys import argv


def get_variables(xml_root):

    variables = []
    for param in xml_root.findall(".//*[.='Define Variable']/..parameters"):
        name = param[0].get('tag')
        value = param[0].get('value')
        description = param[0].get('desc')
        variables.append((name, value, description))

    return variables


def get_experiments(xml_root):
    return xml_root.findall(".//*[.='normal']/..")

def print_experiments_with_parameters(xml_root):
    for experiment in get_experiments(xml_root):
        name = experiment.find('name').text
        parameters = experiment.find('parameters')

        print('-'*50)
        print(name)
        for param in parameters:
            notes = param.get('tag')
            print(notes)



def populate_model_recursively(xml_element, parent_item):
    
    for child in xml_element:
        if child.tag == 'element':
            name_text = child.find('name').text if child.find('name') is not None else 'Brak'
            parameters = get_parameters(child)

            current_item = QStandardItem(name_text)
            current_item.setData(parameters, Qt.UserRole)
            parent_item.appendRow(current_item)

            populate_model_recursively(child, current_item)
            
def get_parameters(element):
    
    new_parameters = []
    parameters = element.find('parameters')
    if parameters:
        for parameter in parameters:
            
            index = parameter.get('index')
            if index:
                chosen_option = 'item' + index
                new_param = {key: value for key, value in parameter.items() 
                             if 'item' not in key or key == chosen_option}
                new_parameters.append(new_param)
            else:
                new_parameters.append(parameter.attrib)
    return new_parameters


class SequenceViewer(QDialog):
    def __init__(self):
        super().__init__()

        layout = QHBoxLayout()
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        self.treeview = QTreeView()
        self.model = QStandardItemModel()
        self.treeview.setModel(self.model)
        splitter.addWidget(self.treeview)

        self.details_display = QTextEdit()
        self.details_display.setPlaceholderText("Choose an element to see its parameters")
        splitter.addWidget(self.details_display)
        splitter.setSizes([300,150])
        
        # Ustawiamy treeview jako centralny widget, żeby był widoczny
        
        self.setLayout(layout)
        self.resize(400, 600)
        self.populate()
        self.treeview.clicked.connect(self.on_select)

    def populate(self):
        # Podmień na prawidłową ścieżkę do pliku
        path = r'D:\!PYTHON\gamry_post_processing_\input\Sequence1.GSequence'
        
        try:
            tree = ET.parse(path)
            root = tree.getroot()

            # Czyszczenie modelu przed ponownym załadowaniem
            self.model.clear()
            # Ustawienie nagłówka kolumny
            self.model.setHorizontalHeaderLabels(['Struktura XML'])

            # Wywołujemy funkcję, przekazując ukryty główny węzeł modelu (invisibleRootItem)
            populate_model_recursively(root, self.model.invisibleRootItem())
            
            # Automatycznie rozwiń drzewo po załadowaniu
            self.treeview.expandAll()
            
        except Exception as e:
            print(f"Błąd podczas ładowania pliku XML: {e}")

    def on_select(self, index):

        custom_data = index.data(Qt.UserRole)
        print(custom_data)
        text_representation = "### TERA TO ### \n\n"
        for dataset in custom_data:
            text_representation += '\n'
            for ix in dataset.values():
                text_representation += f"{ix}\n"

        self.details_display.setText(text_representation)


class VariableSelector(QDialog):
    variableSelected = pyqtSignal(float)

    def __init__(self, parameters_to_set:dict[str:QWidget], sequence_path=None):
        super().__init__()

        # 1. Zmieniamy główny layout na pionowy (QVBoxLayout), 
        #    ponieważ przyciski zazwyczaj chcemy mieć NA DOLE okna.
        main_layout = QVBoxLayout(self)

        # 2. Tworzymy poziomy layout na combobox i etykietę (tak jak miałeś)
        top_layout = QGridLayout()
        main_layout.addLayout(top_layout)

        if sequence_path is None:
            path, _ = QFileDialog.getOpenFileName(self,
            'Choose GSequence', '', filter = 'Gamry GSequence (*.GSequence);; All files (*)')
        else:
            path = sequence_path
        if not path:
            return

        tree = ET.parse(path)    
        root = tree.getroot()

        self.combobox = QComboBox()
        top_layout.addWidget(QLabel('Select Variable:'), 0, 1)
        top_layout.addWidget(self.combobox, 1, 1)

        self.value_label = QLabel()
        top_layout.addWidget(QLabel('Value:'), 0, 2)
        top_layout.addWidget(self.value_label, 1, 2)

        variables = get_variables(root)
        self.populate(variables)

        # Łączenie sygnału zmiany wartości (zabezpieczenie przed None przy starcie)
        self.combobox.currentIndexChanged.connect(self.update_label)
        self.update_label() # Wywołanie na starcie, żeby etykieta od razu pokazała wartość

        self.available_parameters_combobox = QComboBox()
        top_layout.addWidget(QLabel('Parameter to set'), 0, 0)
        top_layout.addWidget(self.available_parameters_combobox, 0, 1)
        self.populate_parameters(parameters_to_set)

        # -------------------------------------------------------------
        # 3. DODAWANIE PRZYCISKÓW (QDialogButtonBox)
        # -------------------------------------------------------------
        # Definiujemy, jakie przyciski chcemy mieć w oknie
        buttons = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        
        self.button_box = QDialogButtonBox(buttons)
        
        # Łączymy sygnały przycisków z wbudowanymi akcjami QDialog
        self.button_box.accepted.connect(self.accept) # Kliknięcie OK wywoła self.accept()
        self.button_box.rejected.connect(self.reject) # Kliknięcie Cancel wywoła self.reject()
        
        # Dodajemy panel z przyciskami na sam dół głównego layoutu
        main_layout.addWidget(self.button_box)
        # -------------------------------------------------------------

        self.setWindowTitle("Variable Selector")
        self.exec()

    def accept(self):
        self.available_parameters_combobox.currentData().setValue(self.get_result())
        super().accept()

    def populate(self, variables):
        for name, value, description in variables:
            self.combobox.addItem(name, value)

    def populate_parameters(self, parameters:dict):
        for name, widget in parameters.items():
            self.available_parameters_combobox.addItem(name, widget)

    def update_label(self):
        # Lambda została przeniesiona do metody dla lepszej czytelności 
        # i uniknięcia błędów, gdy currentData() zwraca typ inny niż string
        data = self.combobox.currentData()
        if data is not None:
            self.value_label.setText(str(data))

    def get_result(self):
        return float(self.combobox.currentData())

if __name__ == '__main__':
    app = QApplication(argv)
    mainwindow = VariableSelector()
    mainwindow.show()
    app.exec_()