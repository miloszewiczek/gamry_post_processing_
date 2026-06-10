from PyQt5.QtWidgets import (QDialog, QDoubleSpinBox, QPushButton, QHBoxLayout, QVBoxLayout, 
                             QDialog, QComboBox, QLabel, QLineEdit, QRadioButton, QButtonGroup,
                            QFormLayout, QGridLayout, QWidget)

from gui.small_widgets import SimpleDoubleSpinBox, BaseDataDialog
from PyQt5.QtCore import QSettings
from gui_PtQt.config import defaults, references
from .reference_manager import ReferenceManagerWindow
from functions.gui_functions import add_category



class AreaDialog(BaseDataDialog):

    def __init__(self, experiments, manager = None, settings_key = "area_dialog_window", parent = None):
        super().__init__(settings_key = settings_key, parent = parent)

        self.experiments = experiments
        self.manager = manager
        settings = QSettings()
        layout = QVBoxLayout()
        label = QLabel('Geometrical Area [cm²]')
        self.value_box = QDoubleSpinBox()
        self.value_box.setRange(0, 1000)
        self.value_box.setDecimals(3)

        self.setLayout(layout)

        #in .json the file contains key-value pairs corresponding to various electrode types
        self.defaults = defaults
        areas = self.defaults.get('electrode_area')

        self.area_layout = QHBoxLayout()
        self.defaults_box = QComboBox()
        self.defaults_box.addItems(areas.keys())
        self.defaults_box.currentTextChanged.connect(lambda x: self.value_box.setValue(areas[x]))


        calculate_from_diameter_btn = QPushButton('From diameter...')
        calculate_from_diameter_btn.clicked.connect(self.init_dialog_box)
        self.area_layout.addWidget(self.defaults_box)
        self.area_layout.addWidget(calculate_from_diameter_btn)

        ok_button = QPushButton('OK')
        ok_button.clicked.connect(self.accept)

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(ok_button)

        #### REFERENCE POTENTIAL
        label_ref = QLabel('Reference potential [V]')

        self.ref_box = QComboBox()

        
        self.populate_electrodes()


        # instead of single value_box, add 3 inputs that correspond to standard potential, offset and pH
        self.reference_value_box = QDoubleSpinBox()
        self.reference_value_box.setRange(0, 1000)
        self.reference_value_box.setDecimals(3)

        self.ref_box.currentTextChanged.connect(self.place_input)

        standard_label = QLabel('Standard E')
        standard_label.setToolTip('defined for pH = 0')
        
        offset_label = QLabel('Offset E')
        offset_label.setToolTip('Taken from calibration vs mother ref electrode. Mostly for AgCl/Ag.')

        pH_label = QLabel('pH')
        pH_label.setToolTip('The potential of Reference Electrode does not depend on the pH. The conversion to RHE does.')

        final_potential_label = QLabel('Final E')
        final_potential_label.setToolTip('Final E = Standard E + Offset E + 0.059*pH')

        Ru_label = QLabel('Uncompensated resistance [Ω]')
        Ru_label.setToolTip('Derived from Get Ru method or EIS measurements. You can right click on EIS experiment and get the Ru value.')

        self.standard_potential_layout = QGridLayout()
        self.standard_potential_layout.addWidget(standard_label, 0, 0)
        self.standard_potential_layout.addWidget(offset_label, 0, 1)
        self.standard_potential_layout.addWidget(pH_label, 0, 2)
        self.standard_potential_layout.addWidget(final_potential_label, 0, 3)

    
        self.standard_potential_DoubleBox = SimpleDoubleSpinBox(0.21)
        self.offset_DoubleBox = SimpleDoubleSpinBox(0)
        self.pH_DoubleBox = SimpleDoubleSpinBox(0, (0,14))
        self.final_potential = SimpleDoubleSpinBox(0)
        self.final_potential.setDisabled(True)
        self.Ru_box = SimpleDoubleSpinBox(0)
        self.Ru_from_EIS_btn = QPushButton('From EIS')
        self.Ru_from_EIS_btn.clicked.connect(self.create_selector)

        self.potentials_list = (self.standard_potential_DoubleBox, self.offset_DoubleBox, self.pH_DoubleBox)
        for component in self.potentials_list:
            component.valueChanged.connect(self.calculate_final_potential)


        self.standard_potential_layout.addWidget(self.standard_potential_DoubleBox, 1, 0)
        self.standard_potential_layout.addWidget(self.offset_DoubleBox, 1, 1)
        self.standard_potential_layout.addWidget(self.pH_DoubleBox, 1, 2)
        self.standard_potential_layout.addWidget(self.final_potential, 1, 3)
        

        self.define_ref_btn = QPushButton('Define')
        self.define_ref_btn.clicked.connect(self.init_reference_manager)
        
        self.ref_box_define_layout = QHBoxLayout()
        self.ref_box_define_layout.addWidget(self.ref_box)
        self.ref_box_define_layout.addWidget(self.define_ref_btn)

        self.Ru_layout = QGridLayout()
        self.Ru_layout.addWidget(self.Ru_box, 1, 0)
        self.Ru_layout.addWidget(Ru_label, 0,0)
        self.Ru_layout.addWidget(self.Ru_from_EIS_btn, 1, 1)
        



        layout.addWidget(label)
        layout.addLayout(self.area_layout)
        layout.addWidget(self.value_box)
        layout.addWidget(label_ref)
        layout.addLayout(self.ref_box_define_layout)
        layout.addLayout(self.standard_potential_layout)
        layout.addLayout(self.Ru_layout)

        layout.addLayout(bottom_layout)

        self.fields = {
            'geometrical_area': self.value_box,
            'electrode_type': self.defaults_box,
            'reference_potential': self.final_potential,
            'standard_potential': self.standard_potential_DoubleBox,
            'offset_potential': self.offset_DoubleBox,
            'pH': self.pH_DoubleBox,
            'Ru': self.Ru_box
        }

    def get_fields(self):
        return self.fields

    def get_data(self):
        """Returns the following dict:\n
        geometrical_area\n
        electrode_type\n
        reference_potential\n
        standard_potential\n
        offset_potential\n
        pH\n
        Ru\n
        """
        return super().get_data()

    def calculate_final_potential(self):
        """
        Calculate potential needed to convert the potential from reference to RHE. Value in [V].
        """

        standard, offset, pH = [component.value() for component in self.potentials_list]
        final_value = standard + offset + 0.059* pH
        self.final_potential_value = round(final_value, 3)
        self.final_potential.setValue(self.final_potential_value)
        return self.final_potential_value
    
    def place_input(self):
        """
        Grab the data from self.ref_box and place it into the Float DoubleBoxes.
        """

        try: # grab the data
            standard_potential, offset_potential = self.ref_box.currentData()

        except: # if the ReferenceManager does not yield appropriate ReferenceElectrode label and offset potential don't do anything
            return
        self.standard_potential_DoubleBox.setValue(standard_potential)
        self.offset_DoubleBox.setValue(offset_potential)

    def populate_electrodes(self):
        """
        Populate the self.ref_box with all electrode types and labels.
        """

        self.ref_box.clear() # clear all the data
        add_category(self.ref_box, 'Standard') #this function gives nice looking separators between electrode types

        # First, standard electrodes are populated from file settings.json
        reference_potentials = self.defaults.get('reference_electrode')
        for standard_electrode, potential in reference_potentials.items():
            self.ref_box.addItem(standard_electrode, (potential,0))

        # Custom electrodes, get them all
        custom_electrodes = references.get_electrode(all = True, group = True)  #this returns a dictionary, because group = True
        if custom_electrodes:
            for electrode_type, electrodes in custom_electrodes.items():
                add_category(self.ref_box, electrode_type)
                for electrode in electrodes:
                    self.ref_box.addItem(electrode.label, (defaults.get('reference_electrode')[electrode.type], electrode.get_calibration_offset()))


    def set_data(self, data: dict[str: QWidget]):
            """Set the widget values based on data from data dictionary."""
            self.blockSignals(True) # Opcjonalnie wycisz całe okno na czas ładowania
            for key, value in data.items():
                widget = self.fields.get(key)
                if not widget: continue

                if isinstance(widget, QDoubleSpinBox):
                    widget.setValue(float(value))
                elif isinstance(widget, QComboBox):
                    index = widget.findText(str(value))
                    if index >= 0:
                        widget.setCurrentIndex(index)
            self.blockSignals(False)

    def init_dialog_box(self):
        area_dialog_box = AreaDialogBox()
        if area_dialog_box.exec() == QDialog.Accepted:
            area_value = area_dialog_box.get_value()
            if area_value:
                self.value_box.setValue(area_dialog_box.get_value())
        else:
            return

    def init_reference_manager(self):
        reference_window = ReferenceManagerWindow()
        if reference_window.exec() == QDialog.Accepted:
            data = reference_window.get_data()
            electrode_label = data['electrode_label']
            calibration_offset = data['calibration_offset']

            self.ref_box.blockSignals(True)
            self.populate_electrodes()
            index = self.ref_box.findText(electrode_label)
            self.ref_box.blockSignals(False)
            self.ref_box.setCurrentIndex(index)

    
    def create_selector(self):
        from .small_widgets import DataSelector
        from experiments import EIS
        def get_value(tuple):
            #we just want the x value!
            self.Ru_box.setValue(tuple[0])
        quick = DataSelector(None)
        quick.setup_data(manager = self.manager, experiments = self.experiments, object_type = EIS)
        quick.myaccepted.connect(get_value)
        quick.exec()

        


class AreaDialogBox(QDialog):
    """
    A simple QDialog class that gets and sets most common parameters such as 
    geometric area, uncompensated resistance (Ru) or reference potential.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calculate Area")
        
        # 1. Wywołanie posegregowanych etapów budowania okna
        self.init_ui()
        self.setup_layouts()
        self.connect_signals()
        
        # Uruchomienie początkowego stanu (opcjonalnie na koniec)
        self.build_ui() 

    def init_ui(self):
        """KROK 1: Definicje i konfiguracja wszystkich widgetów i struktur danych."""
        self.main_layout = QVBoxLayout(self)
        
        self.label_units = QLabel('Area type')
        self.units = QComboBox()
        self.units.addItems(['cm', 'mm', 'm'])
        
        # Pola wprowadzania danych
        self.circle_diameter = QLineEdit()
        self.square_length = QLineEdit()
        self.square_length.setDisabled(True)
        self.rectangle_a = QLineEdit()
        self.rectangle_b = QLineEdit() 
        self.rectangle_a.setDisabled(True)
        self.rectangle_b.setDisabled(True)

        # Radio buttony
        self.circle_radio = QRadioButton('Circle')
        self.circle_radio.setChecked(True)
        self.square_radio = QRadioButton('Square')
        self.rectangle_radio = QRadioButton('Rectangle')
        
        self.radio_group = QButtonGroup()
        self.radio_group.addButton(self.circle_radio)
        self.radio_group.addButton(self.square_radio)
        self.radio_group.addButton(self.rectangle_radio)

        # Widgety wynikowe i przyciski akcji
        self.result_string = QLabel('Calculated Area: ')
        self.result_value = QLabel('0')
        self.ok_button = QPushButton('OK')

        # Słowniki mapujące (Logika biznesowa UI)
        self.widget_dict = {
            self.circle_radio: (self.circle_diameter,),
            self.square_radio: (self.square_length,),
            self.rectangle_radio: (self.rectangle_a, self.rectangle_b)
        }
        self.method_dict = {
            self.circle_radio: self.calculate_circle_area,
            self.square_radio: self.calculate_square_area,
            self.rectangle_radio: self.calculate_rectangle_area
        }

    def setup_layouts(self):
        """KROK 2: Budowanie struktury layoutów (Wszystkie addWidget w jednym miejscu)."""
        self.main_layout.addWidget(self.label_units)
        self.main_layout.addWidget(self.units)
        
        # Kontenery/Layouty dla poszczególnych figur
        self.circle_layout = QHBoxLayout()
        self.circle_layout.addWidget(self.circle_diameter)
        
        self.square_layout = QHBoxLayout()
        self.square_layout.addWidget(self.square_length)
        
        self.rectangle_layout = QHBoxLayout()
        self.rectangle_layout.addWidget(self.rectangle_a)
        self.rectangle_layout.addWidget(self.rectangle_b)

        # Łączenie sekcji figur w głównym layoucie
        self.main_layout.addWidget(self.circle_radio)
        self.main_layout.addLayout(self.circle_layout)
        
        self.main_layout.addWidget(self.square_radio)
        self.main_layout.addLayout(self.square_layout)
        
        self.main_layout.addWidget(self.rectangle_radio)
        self.main_layout.addLayout(self.rectangle_layout)

        # Sekcja wyniku
        self.result_layout = QHBoxLayout()
        self.result_layout.addWidget(self.result_string)
        self.result_layout.addWidget(self.result_value)
        self.main_layout.addLayout(self.result_layout)
        
        # Dół okna
        self.main_layout.addWidget(self.ok_button)

    def connect_signals(self):
        """KROK 3: Połączenia sygnałów ze slotami."""
        self.circle_diameter.textChanged.connect(self.calculate_circle_area)
        self.square_length.textChanged.connect(self.calculate_square_area)
        self.rectangle_a.textChanged.connect(self.calculate_rectangle_area)
        self.rectangle_b.textChanged.connect(self.calculate_rectangle_area)
        
        self.radio_group.buttonClicked.connect(self.on_button_clicked)
        self.ok_button.clicked.connect(self.accept)
        
        # Zmiana jednostki też powinna przeliczyć widok na żywo!
        # self.units.currentTextChanged.connect(self.recalculate_current)

    def on_button_clicked(self, clicked_button):
        # Iterujemy po słowniku tylko raz
        for radio_button, widgets in self.widget_dict.items():
            # Sprawdzamy, czy to ten kliknięty przycisk
            is_active = (radio_button == clicked_button)
            
            for widget in widgets:
                widget.setEnabled(is_active)
            
            if is_active is True:
                area_function = self.method_dict[radio_button]
                area_function() 
    
    def calculate_circle_area(self):
        try:
            diameter = float(self.circle_diameter.text())
        except:
            self.result_value.setText("") 
            return
        area = 3.14 * diameter**2 / 4
        self.set_area(area)
    
    def calculate_rectangle_area(self):
        try:
            a,b  = float(self.rectangle_a.text()), float(self.rectangle_b.text())
        except:
            self.result_value.setText("") 
            return
        
        area = a * b
        self.set_area(area)

    def calculate_square_area(self):
        try:
            a = float(self.square_length.text())
        except:
            self.result_value.setText("") 
            return
        area = a**2
        self.set_area(area)


    def set_area(self, area):
        self.area = area
        self.result_value.setText(str(area) + " " + self.units.currentText() + "\u00B2")
       
    def get_value(self):
        try:
            return self.area
        except:
            return

