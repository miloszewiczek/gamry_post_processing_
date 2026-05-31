from contextlib import contextmanager
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QPushButton, QComboBox, QLabel, QGroupBox, QLineEdit, QShortcut
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtCore import Qt
from experiments import Voltammetry, LinearVoltammetry
from gui.small_widgets import TreeSelectorWithCheckboxes, SimpleDoubleSpinBox, Selector, SelectorWithSample
from gui_PtQt.plotting_area import DoubleLayerCanvas
from functions.functions import calc_first
import matplotlib.cm as cm


class OverpotentialsWindow(QDialog):
    def __init__(self, experiments, parent = None):
        super().__init__(parent)
        

        self.current_density_label = QLabel('Current density [A/cm²]')
        line_edit_layout = QHBoxLayout()
        self.line_edit = QLineEdit()
        self.unit_combobox = QComboBox()
        line_edit_layout.addWidget(self.line_edit)
        line_edit_layout.addWidget(self.unit_combobox)

        units = [
            ('A/cm²', 1.0),
            ('mA/cm²', 0.001),
            ('µA/cm²', 0.000001)
        ]

        for text, multiplier in units:
            self.unit_combobox.addItem(text, multiplier)
        self.unit_combobox.setCurrentText('mA/cm²')

        self.addCurrents = QPushButton('Add')
        self.addCurrents.clicked.connect(self.strip)
        self.line_edit.returnPressed.connect(self.strip)
        self.reset_btn = QPushButton('Reset')
        self.reset_btn.clicked.connect(self.reset)
        self.reset_btn.setAutoDefault(False)
        self.reset_btn.setDefault(False)

        main_layout = QVBoxLayout()
        reference_potentials = QComboBox()
        reference_potentials.addItems(['0 V', '-0.15 V', '0.20 V', '0.6 V'])
        reference_potentials.currentTextChanged.connect(self.line_edit.setText)

        self.densities_layout = QVBoxLayout()
        self.densities = []

        main_layout.addWidget(reference_potentials)
        main_layout.addLayout(line_edit_layout)
        main_layout.addWidget(self.current_density_label)
        main_layout.addLayout(self.densities_layout)
        main_layout.addWidget(self.reset_btn)
        self.setLayout(main_layout)
        self.line_edit.setFocus()



    def strip(self):
        

        data_string = self.line_edit.text()
        if data_string:
            data_string.strip()
            split_string = data_string.split()
            for density in split_string:
                try:
                    float_density = float(density)
                    float_density_in_amps = float_density * self.unit_combobox.currentData()
                except:
                    continue
                widget_to_add = QLineEdit(str(float_density_in_amps))
                self.densities_layout.addWidget(widget_to_add)
                self.densities.append((widget_to_add, float_density_in_amps))
            
            self.line_edit.clear()

    def reset(self):

        for widget, _ in self.densities:
            self.densities_layout.removeWidget(widget)
            widget.deleteLater()

        self.densities.clear()

        # Line for user to check 
        #define a list (maybe in settings or sth) for user to select e.g. RHE is 0 V (but it moves with pH!)

        