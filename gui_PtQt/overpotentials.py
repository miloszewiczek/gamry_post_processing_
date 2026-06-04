from contextlib import contextmanager
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QPushButton, QComboBox, QLabel, QGroupBox, QLineEdit, QShortcut, QVBoxLayout, QMessageBox
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtCore import Qt
from experiments import Voltammetry, LinearVoltammetry
from gui.small_widgets import TreeSelectorWithCheckboxes, SimpleDoubleSpinBox, Selector, SelectorWithSample
from gui_PtQt.plotting_area import DoubleLayerCanvas
from functions.functions import calc_closest_value, convert_to_overpotential_scale
import matplotlib.cm as cm
from experiments.sample import Sample
from experiments import Experiment 
import pandas as pd
from experiments.analysis import OverpotentialAnalysis
from core import ExperimentManager


class OverpotentialsWindow(QDialog):
    def __init__(self, sample_dict:dict[Sample, list[Experiment]], parent = None, manager:ExperimentManager = None):
        super().__init__(parent)
        
        self.manager = manager
        self.current_density_label = QLabel('Current density [A/cm²]')
        line_edit_layout = QHBoxLayout()
        self.line_edit = QLineEdit()
        self.unit_combobox = QComboBox()
        line_edit_layout.addWidget(self.line_edit)
        line_edit_layout.addWidget(self.unit_combobox)

        self.bootstrap_data(sample_dict)
        self.selector = SelectorWithSample(sample_dict)

        # Since we go to A/cm2, we have to divide by 1000 or multiply by 0.001
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


        reference_potentials = [('RHE', 0),
                                ('OER', 1.23),
                                ('Custom', 0)]

        self.reference_potentials = QComboBox()
        for name, potential in reference_potentials:
            self.reference_potentials.addItem(name, potential)

        self.reference_potential_line_edit = SimpleDoubleSpinBox(0)
        self.reference_potential_line_edit.setEnabled(False)

        self.reference_potentials.currentTextChanged.connect(self.update_reference_potential)
        self.densities = []
        self.calculate_btn = QPushButton('Calculate!')
        self.calculate_btn.clicked.connect(self.calculate_overpotentials)
        self.setup_gui()

    def update_reference_potential(self):
        current_text = self.reference_potentials.currentText()
        if current_text == 'Custom':
            self.reference_potential_line_edit.setEnabled(True)
        else:
            self.reference_potential_line_edit.setEnabled(False)
            self.reference_potential_line_edit.setValue(self.reference_potentials.currentData())

    def setup_gui(self):
        
        reference_potentials_labels_layout = QHBoxLayout()
        reference_potentials_labels_layout.addWidget(QLabel('Electrode reaction'))
        reference_potentials_labels_layout.addWidget(QLabel('Electrode potential [V]'))

        reference_potentials_layout = QHBoxLayout()
        reference_potentials_layout.addWidget(self.reference_potentials)
        reference_potentials_layout.addWidget(self.reference_potential_line_edit)

        current_densities_layout = QHBoxLayout()
        current_densities_layout.addWidget(QLabel('Current densities to add: '))
        current_densities_layout.addWidget(self.line_edit)
        current_densities_layout.addWidget(self.unit_combobox)
        current_densities_layout.addWidget(self.addCurrents)

        button_layout = QHBoxLayout()
        button_layout.addWidget(QLabel('Chosen current densities [A/cm²]'))
        button_layout.addWidget(self.reset_btn)
        button_layout.addWidget(self.calculate_btn)

        self.chosen_current_densities_layout = QVBoxLayout()        

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.selector)
        main_layout.addLayout(reference_potentials_labels_layout)
        main_layout.addLayout(reference_potentials_layout)
        main_layout.addLayout(current_densities_layout)
        main_layout.addLayout(button_layout)
        main_layout.addLayout(self.chosen_current_densities_layout)

        self.setLayout(main_layout)
        self.line_edit.setFocus()

    def bootstrap_data(self, sample_dict):
        for sample, experiments in sample_dict.items():
            self.manager.is_processed(experiments)


    def calculate_overpotentials3(self):

        sample_experiments_dict = self.selector.get_experiments_to_analysis()
        point_to_calc = [float(widget.text()) for widget in self.densities]

        for sample, experiments in sample_experiments_dict.items():

            data = {exp.file_name: exp.get_xy_data(0) for exp in experiments}
            
            test = []
            
            # x is potential, y is current density
            for (x, y) in data.values():

                #we want to calculate overpotential, so we search for x values!!!
                val = calc_closest_value(point_to_calc, y, x, 'first')
                test.append(val)
            df = pd.DataFrame(test, columns = point_to_calc, index = list(data.keys()))
            overpotentials_vs_reference = df - self.reference_potential_line_edit.value()
            print(overpotentials_vs_reference.mean(0))

            x = OverpotentialAnalysis(sample.sample_name, experiments= experiments, data = overpotentials_vs_reference)

    def calculate_overpotentials(self):
        sample_experiments_list = self.selector.get_flat_list()
        sample_experiments_dict = self.manager.construct_tree_with_cycles(sample_experiments_list)

        point_to_calc = [float(widget.text()) for widget in self.densities]


        # Listy, w których zbierzemy dane z CAŁEGO folderu / wszystkich próbek
        all_rows_data = []
        multi_index_tuples = []

        for sample, cycle_dict in sample_experiments_dict.items():
            for cycle_num, experiments in cycle_dict.items():
                for exp in experiments:
                # Pobieramy dane eksperymentu
                    x, y = exp.get_xy_data(0)

                    
                    # Liczymy zbliżone wartości dla zadanych prądów
                    val = calc_closest_value(point_to_calc, y, x, 'first')
                    all_rows_data.append(val)

                    # WYCIĄGANIE CYKLU: zakładam, że obiekt exp ma atrybut .cycle 
                    # Jeśli nie ma, możesz użyć bezpiecznego wyciągania: getattr(exp, 'cycle', 1)
                    
                    # Tworzymy krotkę identyfikującą ten konkretny wiersz w hierarchii
                    # Sample Name -> Cycle -> File Name
                    index_tuple = (sample.sample_name, f"Cycle {cycle_num}", exp.file_name)
                    multi_index_tuples.append(index_tuple)

        # Zabezpieczenie na wypadek, gdyby użytkownik nic nie zaznaczył
        if not all_rows_data:
            print("No experiments selected.")
            return

        # 1. Tworzymy obiekt MultiIndex z zebranych krotek
        m_index = pd.MultiIndex.from_tuples(
            multi_index_tuples, 
            names=['Sample', 'Cycle', 'Experiment']
        )

        # 2. Tworzymy JEDEN zbiorczy DataFrame dla całej analizy!
        full_df = pd.DataFrame(all_rows_data, columns=point_to_calc, index=m_index)
        
        # 3. Odejmujemy potencjał odniesienia (Pandas odejmie go automatycznie od każdej komórki)
        overpotentials_vs_reference = full_df - self.reference_potential_line_edit.value()
        

        x = OverpotentialAnalysis('Analysis 1', experiments = sample_experiments_dict, data = overpotentials_vs_reference)

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
                self.chosen_current_densities_layout.addWidget(widget_to_add)
                self.densities.append(widget_to_add)
            
            self.line_edit.clear()

    def reset(self):

        for widget in self.densities:
            self.chosen_current_densities_layout.removeWidget(widget)
            widget.deleteLater()

        self.densities.clear()

        # Line for user to check 
        #define a list (maybe in settings or sth) for user to select e.g. RHE is 0 V (but it moves with pH!)

        