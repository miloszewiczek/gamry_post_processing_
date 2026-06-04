from contextlib import contextmanager
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QPushButton, QComboBox, QLabel, QGroupBox
from PyQt5.QtCore import Qt
from experiments import Voltammetry, ECSA
from gui.small_widgets import TreeSelectorWithCheckboxes, SimpleDoubleSpinBox, Selector, SelectorWithSample
from gui_PtQt.plotting_area import DoubleLayerCanvas
from functions.functions import calculate_ECSA_from_slope
import matplotlib.cm as cm
from core import ExperimentManager
from experiments.analysis import DoubleLayerAnalysis


class DoubleLayer(QDialog):
    def __init__(self, selected_indices, parent=None, manager: ExperimentManager = None):
        super().__init__(parent)
        self.setWindowTitle("Double Layer Capacity & ECSA Calculation")
        self.resize(1100, 600)  # Szeroki, panoramiczny layout pod dwa wykresy i drzewo
        
        self.manager = manager
        self.experiments = []
        
        # 1. Wstępne ładowanie i procesowanie surowych danych (Bootstrap)
        self._bootstrap_data(selected_indices)
        num_samples = len(selected_indices.keys())
        self.cmap = cm.get_cmap('Set1', num_samples*2)   

        # 2. Inicjalizacja komponentów interfejsu
        # Przekazujemy model nadrzędny i indeksy bezpośrednio do selektora z checkboxami
        self.selector = SelectorWithSample(selected_indices)
        self.canvas = DoubleLayerCanvas()
        self.potential_spinbox = SimpleDoubleSpinBox(0, None)
        self.curve_combobox = QComboBox()
        self.calculate_btn = QPushButton("Calculate CDL")
        
        self.init_gui()
        self.connect_signals()
        
        # 3. Pierwsze wymuszenie renderu stanu okna
        self.refresh_ui_state()

    @contextmanager
    def signals_blocked(self, widget):
        """Bezpieczny menedżer kontekstu do blokowania sygnałów."""
        widget.blockSignals(True)
        try:
            yield
        finally:
            widget.blockSignals(False)

    def _bootstrap_data(self, selected_indices):
        """Wstępne ładowanie i procesowanie danych na bazie zaznaczonych indeksów."""
        for sample, experiments in selected_indices.items():
            
            for ECSA_experiment in experiments:
            # Jeśli w drzewie zaznaczono bezpośrednio obiekt typu ECSA lub Voltammetry, sprawdzamy go
                if isinstance(ECSA_experiment, (ECSA, Voltammetry)):
                    if not hasattr(ECSA_experiment, "data_list"):
                        ECSA_experiment.load_all()
                    if not hasattr(ECSA_experiment, 'processed_data'):
                        ECSA_experiment.process_data()


    def init_gui(self):
        # Główny układ: Lewa strona (Kontrolki) | Prawa strona (Wykres panoramiczny)
        main_layout = QHBoxLayout(self)
        control_layout = QVBoxLayout()
        
        # Panel wyboru eksperymentów z checkboxami
        control_layout.addWidget(QLabel("<b>Select Experiments:</b>"))
        control_layout.addWidget(self.selector)
        
        # Panel parametrów zgrupowany w ramkę QGroupBox
        settings_group = QGroupBox("Plotting & Analysis Settings")
        settings_layout = QVBoxLayout(settings_group)
        
        settings_layout.addWidget(QLabel("Select Curve Index:"))
        settings_layout.addWidget(self.curve_combobox)
        
        settings_layout.addWidget(QLabel("Potential value [V]:"))
        settings_layout.addWidget(self.potential_spinbox)
        
        settings_layout.addWidget(self.calculate_btn)
        
        control_layout.addWidget(settings_group)
        
        # Proporcje (Zajętość ekranu): panel boczny 2, wykres dwupanelowy Matplotlib 3
        main_layout.addLayout(control_layout, stretch=2)
        main_layout.addWidget(self.canvas, stretch=3)

    def connect_signals(self):
        # Sygnał z Twojej nowej klasy checkboxów - odświeża stan okna przy każdym kliknięciu ptaszka
        self.selector.item_changed.connect(self.refresh_ui_state)
        
        self.curve_combobox.currentIndexChanged.connect(self.replotted_selected_curve)
        self.calculate_btn.clicked.connect(self.run_cdl_calculation)
        
        # Interaktywna linia vline: zmiana wartości w spinboxie od razu przesuwa kreskę na wykresie CV
        self.potential_spinbox.valueChanged.connect(self.canvas.move_vline)

    def refresh_ui_state(self):
        """Zarządza stanem kontrolek w zależności od wybranego eksperymentu."""
        self.experiments_dict = self.selector.get_experiments_to_analysis()
        experiments = self.experiments_dict.values()
        self.experiments = [exp for exp_list in self.experiments_dict.values() for exp in exp_list]

        if not self.experiments:
            with self.signals_blocked(self.curve_combobox):
                self.curve_combobox.clear()
                self.curve_combobox.setCurrentText('Add an experiment to analysis')
                self.curve_combobox.setDisabled(True)
                self.calculate_btn.setDisabled(True)
            self.canvas.clear_all()
            return

        self.curve_combobox.setDisabled(False)
        self.calculate_btn.setDisabled(False)
        
        # Aktualizacja zawartości ComboBoxa (zakres dostępnych cykli)
        available_curves = self.get_common_curve_indices()
        previous_selection = self.curve_combobox.currentText()
        
        with self.signals_blocked(self.curve_combobox):
            self.curve_combobox.clear()
            self.curve_combobox.addItems(available_curves)

            if previous_selection in available_curves:
                self.curve_combobox.setCurrentText(previous_selection)
            elif available_curves:
                self.curve_combobox.setCurrentIndex(0)
                
        self.replotted_selected_curve()
        
        # AUTOMATYKA: Ustawia spinbox na optymalną wartość środkową (half potential) pierwszej krzywej
        if hasattr(self.experiments[0], 'get_half_potential'):
            self.potential_spinbox.setValue(self.experiments[0].get_half_potential())

    def replotted_selected_curve(self):
        """Odświeża tylko lewy wykres (Krzywe CV)."""
        self.canvas.clear_except_line()

        raw_text = self.curve_combobox.currentText()
        if raw_text and raw_text.isdigit() and self.experiments_dict:
            selected_curve = [int(raw_text)]
            flat_experiment_list = self.selector.get_flat_list()
            cycle_experiment_dict = self.manager.construct_tree_with_cycles(flat_experiment_list)
            for sample, cycle_dict in cycle_experiment_dict.items():
                for i, (cycle_num, experiments) in enumerate(cycle_dict.items()):
                    
                    data_to_plot = {experiment: experiment.get_plot_data(selected_curve) for experiment in experiments}
                    self.canvas.plot_cv_curves(data_to_plot, color = self.cmap(i))

    def get_current_indexes(self):
        raw_text = self.curve_combobox.currentText()
        if raw_text and raw_text.isdigit():
            return [int(raw_text)]
        return None

    def get_common_curve_indices(self):
        """Oblicza bezpieczny wspólny zakres krzywych (cykli) dla wybranych plików."""
        if not self.experiments:
            return []
        min_len = min(len(exp.data_list) for exp in self.experiments if hasattr(exp, 'data_list'))
        return [str(i) for i in range(min_len)]

    def run_cdl_calculation(self):
        """Pobiera parametry, liczy nachylenie i rysuje prawy wykres."""
        if not self.experiments:
            return

        self.canvas.ax_cdl.clear()            
        chosen_potential = self.potential_spinbox.value()
        current_index = self.get_current_indexes()
        if current_index is None:
            return
        

        flat_experiment_list = self.selector.get_flat_list()
        cycle_experiment_dict = self.manager.construct_tree_with_cycles(flat_experiment_list)

        new_dict = {}
        for sample, cycle_dict in cycle_experiment_dict.items():
            new_dict[sample] = {}

            for i, (cycle_num, experiments) in enumerate(cycle_dict.items()):
                new_dict[sample][cycle_num] = {}
                results_dict = calculate_ECSA_from_slope(
                    ECSA_experiments = experiments, 
                    potential =chosen_potential, 
                    index = current_index
            )        
                
            # Rysujemy proste dopasowania CDL na prawej połówce DoubleLayerCanvas
                self.canvas.plot_cdl_fit(sample.short_name, results_dict, color = self.cmap(i))


                x = DoubleLayerAnalysis(name = sample.sample_name, 
                                        cycle = cycle_num,
                                        experiments = experiments,
                                        fitting_data = results_dict['df_fitting'],
                                        raw_data = results_dict['df_data'],
                                        potential = chosen_potential)
        