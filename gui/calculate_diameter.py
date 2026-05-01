from PyQt5.QtWidgets import QDialog, QDoubleSpinBox, QPushButton, QHBoxLayout, QVBoxLayout, QDialog, QComboBox, QLabel, QLineEdit, QRadioButton, QButtonGroup
from gui_PtQt.config import settings, references
from .reference_manager import ReferenceManagerWindow
from functions.gui_functions import add_category


class AreaDialog(QDialog):
    def __init__(self):
        super().__init__()


        layout = QVBoxLayout()
        label = QLabel('Geometrical Area [cm2]')
        self.value_box = QDoubleSpinBox()
        self.value_box.setRange(0, 1000)
        self.value_box.setDecimals(3)
        self.value_box.setValue(0.196)

        self.setLayout(layout)

        #in .json the file contains key-value pairs corresponding to various electrode types
        self.settings = settings
        areas = self.settings.get('electrode_area')
        defaults_box = QComboBox()
        defaults_box.addItems(areas.keys())
        defaults_box.currentTextChanged.connect(lambda x: self.value_box.setValue(areas[x]))
        

        calculate_from_diameter_btn = QPushButton('From diameter...')
        calculate_from_diameter_btn.clicked.connect(self.init_dialog_box)

        ok_button = QPushButton('OK')
        ok_button.clicked.connect(self.accept)

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(calculate_from_diameter_btn)
        bottom_layout.addWidget(ok_button)

        #### REFERENCE POTENTIAL
        label_ref = QLabel('Reference potential [V]')
        reference_potentials = self.settings.get('reference_electrode')
        self.ref_box = QComboBox()

        add_category(self.ref_box, 'Standard')
        
        for standard_electrode, potential in reference_potentials.items():
            self.ref_box.addItem(standard_electrode, potential)

        custom_electrodes = references.get_electrode(all = True, group = True)
        if custom_electrodes:
            for electrode_type, electrodes in custom_electrodes.items():
                add_category(self.ref_box, electrode_type)
                for electrode in electrodes:
                    self.ref_box.addItem(electrode.label, electrode.get_calibration_offset())


        # instead of single value_box, add 3 inputs that correspond to standard potential, offset and pH
        self.reference_value_box = QDoubleSpinBox()
        self.reference_value_box.setRange(0, 1000)
        self.reference_value_box.setDecimals(3)
        self.reference_value_box.setValue(0.210)


        self.ref_box.currentTextChanged.connect(lambda x: self.reference_value_box.setValue(self.ref_box.currentData()))

        self.define_ref_btn = QPushButton('Define')
        self.define_ref_btn.clicked.connect(self.init_reference_manager)
        
        
        layout.addWidget(label)
        layout.addWidget(defaults_box)
        layout.addWidget(self.value_box)

        layout.addWidget(label_ref)
        layout.addWidget(self.ref_box)
        layout.addWidget(self.define_ref_btn)
        layout.addWidget(self.reference_value_box)

        layout.addLayout(bottom_layout)


    def get_value(self):
        return self.value_box.value()

    def init_dialog_box(self):
        x = AreaDialogBox()
        if x.exec() == QDialog.Accepted:
            self.value_box.setValue(x.get_value())
        else:
            print('none')

    def init_reference_manager(self):
        x = ReferenceManagerWindow()
        if x.exec() == QDialog.Accepted:
            electrode_type, offset = x.get_data()

            self.ref_box.setItemText(electrode_type)
            current_potential = self.reference_value_box.value()
            potential_with_offset = current_potential + offset
            self.reference_value_box.setValue(potential_with_offset)

        


class AreaDialogBox(QDialog):
    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)
        label = QLabel('Area type')
        self.units = QComboBox()
        self.units.addItems(['cm', 'mm', 'm'])
        
        self.layout.addWidget(label)
        self.layout.addWidget(self.units)
        
        self.circle_layout = QHBoxLayout()
        self.circle_diameter = QLineEdit()
        self.circle_diameter.textChanged.connect(self.calculate_circle_area)
        self.circle_layout.addWidget(self.circle_diameter)

        self.square_layout = QHBoxLayout()
        self.square_length = QLineEdit()
        self.square_length.textChanged.connect(self.calculate_square_area)
        self.square_length.setDisabled(True)
        self.square_layout.addWidget(self.square_length)

        self.rectangle_layout = QHBoxLayout()
        self.rectangle_a = QLineEdit()
        self.rectangle_b = QLineEdit() 
        self.rectangle_a.textChanged.connect(self.calculate_rectangle_area)
        self.rectangle_b.textChanged.connect(self.calculate_rectangle_area)
        self.rectangle_a.setDisabled(True)
        self.rectangle_b.setDisabled(True)

        self.rectangle_layout.addWidget(self.rectangle_a)
        self.rectangle_layout.addWidget(self.rectangle_b)

        self.circle_radio = QRadioButton('Circle')
        self.circle_radio.setChecked(True)
        self.square_radio = QRadioButton('Square')
        self.rectangle_radio = QRadioButton('Rectangle')
        self.radio_group = QButtonGroup()
        self.radio_group.addButton(self.circle_radio)
        self.radio_group.addButton(self.square_radio)
        self.radio_group.addButton(self.rectangle_radio)
        self.radio_group.buttonClicked.connect(self.on_button_clicked)

        self.ok_button = QPushButton('OK')
        self.ok_button.clicked.connect(self.accept)

        self.layout.addWidget(self.circle_radio)
        self.layout.addLayout(self.circle_layout)
        self.layout.addWidget(self.square_radio)
        self.layout.addLayout(self.square_layout)
        self.layout.addWidget(self.rectangle_radio)
        self.layout.addLayout(self.rectangle_layout)
        

        self.result_layout = QHBoxLayout()
        self.result_string = QLabel('Calculated Area: ')
        self.result_value = QLabel('0')
        self.result_layout.addWidget(self.result_string)
        self.result_layout.addWidget(self.result_value)
        self.layout.addLayout(self.result_layout)
        
        self.layout.addWidget(self.ok_button)

        self.widget_dict = {self.circle_radio: (self.circle_diameter,),
                            self.square_radio: (self.square_length,),
                            self.rectangle_radio: (self.rectangle_a, self.rectangle_b)
        }
        self.method_dict = {self.circle_radio: self.calculate_circle_area,
                    self.square_radio: self.calculate_square_area,
                    self.rectangle_radio: self.calculate_rectangle_area
        }



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



        
