from contextlib import contextmanager
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QPushButton, QComboBox, QLabel, QGroupBox, QWidget
from PyQt5.QtCore import Qt
from experiments import Voltammetry, ECSA
from gui.small_widgets import TreeSelectorWithCheckboxes, SimpleDoubleSpinBox, Selector, SelectorWithSample
from gui_PtQt.plotting_area import DoubleLayerCanvas
from functions.functions import calculate_ECSA_from_slope
import matplotlib.cm as cm
from core import ExperimentManager
from experiments.analysis import DoubleLayerAnalysis


class DoubleLayerDialog(QDialog):
    """Tradycyjne okno z drzewem wyboru dla użytkownika."""
    def __init__(self, selected_indices, manager=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Double Layer Capacity & ECSA Calculation")
        self.resize(1200, 600)
        
        # Komponenty
        self.selector = SelectorWithSample(selected_indices)
        self.analysis_widget = DoubleLayerCoreWidget(manager=manager)
        
        # Układ: Doklejamy selektor z lewej strony rdzenia obliczeniowego
        layout = QHBoxLayout(self)
        
        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("<b>Select Experiments:</b>"))
        left_panel.addWidget(self.selector)
        
        layout.addLayout(left_panel, stretch=2)
        layout.addWidget(self.analysis_widget, stretch=4)
        
        # Łączenie: Zmiana w selektorze pcha dane do rdzenia
        self.selector.item_changed.connect(self.update_analysis_data)
        
        # Pierwsze załadowanie danych
        self.update_analysis_data()

    def update_analysis_data(self):
        # Pobieramy słownik z selektora i przekazujemy "głębiej"
        data = self.selector.get_experiments_to_analysis()
        self.analysis_widget.set_experiments(data)
 



class DoubleLayerCoreWidget(QWidget):
    """
    Serce analizy. Nie posiada selektora danych. 
    Wymaga podania gotowego słownika z eksperymentami przez metodę 'set_experiments'.
    """
    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.experiments_dict = {}
        self.experiments = []
        self.cmap = None
        
        # Inicjalizacja czystego interfejsu (bez selektora)
        self.canvas = DoubleLayerCanvas()
        self.potential_spinbox = SimpleDoubleSpinBox(0, None)
        self.curve_combobox = QComboBox()
        self.calculate_btn = QPushButton("Calculate CDL")
        
        self.init_gui()
        self.connect_signals()

    @contextmanager
    def signals_blocked(self, widget):
        """Bezpieczny menedżer kontekstu do blokowania sygnałów."""
        widget.blockSignals(True)
        try:
            yield
        finally:
            widget.blockSignals(False)

    def init_gui(self):
        main_layout = QHBoxLayout(self)
        control_layout = QVBoxLayout()
        
        # Panel parametrów
        settings_group = QGroupBox("Plotting & Analysis Settings")
        settings_layout = QVBoxLayout(settings_group)
        settings_layout.addWidget(QLabel("Select Curve Index:"))
        settings_layout.addWidget(self.curve_combobox)
        settings_layout.addWidget(QLabel("Potential value [V]:"))
        settings_layout.addWidget(self.potential_spinbox)
        settings_layout.addWidget(self.calculate_btn)
        
        control_layout.addWidget(settings_group)
        control_layout.addStretch() # Spycha kontrolki do góry
        
        main_layout.addLayout(control_layout, stretch=2)
        main_layout.addWidget(self.canvas, stretch=3)

    def connect_signals(self):
        self.curve_combobox.currentIndexChanged.connect(self.replotted_selected_curve)
        self.calculate_btn.clicked.connect(self.run_cdl_calculation)
        self.potential_spinbox.valueChanged.connect(self.canvas.move_vline)

    def set_experiments(self, experiments_dict):
        """Metoda wejściowa dla danych z zewnątrz (Wizarda lub Selektora)."""
        self.experiments_dict = experiments_dict if experiments_dict else {}
        self.experiments = [exp for exp_list in self.experiments_dict.values() for exp in exp_list]
        
        # Dynamiczne ustawienie colormapy na bazie wstrzykniętych danych
        num_samples = len(self.experiments_dict.keys())
        self.cmap = cm.get_cmap('Set1', max(num_samples * 2, 1))
        
        # Uruchomienie oryginalnej logiki odświeżania UI
        self.refresh_ui_state()

    def refresh_ui_state(self):
        """Zarządza stanem kontrolek w zależności od wybranego eksperymentu."""
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
        
        # AUTOMATYKA: Bezpieczne ustawienie spinboxa bez wywoływania przedwczesnych sygnałów rysowania
        if hasattr(self.experiments[0], 'get_half_potential'):
            x = self.experiments[0].get_half_potential()
            with self.signals_blocked(self.potential_spinbox):
                self.potential_spinbox.setValue(x)
            # Ręcznie przesuwamy kreskę na wykresie po bezpiecznej zmianie wartości
            self.canvas.move_vline(x)

    def replotted_selected_curve(self):
        """Odświeża tylko lewy wykres (Krzywe CV)."""
        self.canvas.clear_except_line()

        raw_text = self.curve_combobox.currentText()
        if raw_text and raw_text.isdigit() and self.experiments_dict:
            selected_curve = [int(raw_text)]
            
            # POPRAWKA: Słownik nie ma metody get_flat_list(), spłaszczamy go ręcznie:
            flat_experiment_list = [exp for exp_list in self.experiments_dict.values() for exp in exp_list]
            
            cycle_experiment_dict = self.manager.construct_tree_with_cycles(flat_experiment_list)
            for sample, cycle_dict in cycle_experiment_dict.items():
                for i, (cycle_num, experiments) in enumerate(cycle_dict.items()):
                    data_to_plot = {experiment: experiment.get_plot_data(selected_curve) for experiment in experiments}
                    self.canvas.plot_cv_curves(data_to_plot, color=self.cmap(i))

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
        
        # POPRAWKA: Słownik nie ma metody get_flat_list(), spłaszczamy go ręcznie:
        flat_experiment_list = [exp for exp_list in self.experiments_dict.values() for exp in exp_list]
        
        cycle_experiment_dict = self.manager.construct_tree_with_cycles(flat_experiment_list)

        new_dict = {}
        for sample, cycle_dict in cycle_experiment_dict.items():
            new_dict[sample] = {}

            for i, (cycle_num, experiments) in enumerate(cycle_dict.items()):
                new_dict[sample][cycle_num] = {}
                results_dict = calculate_ECSA_from_slope(
                    ECSA_experiments=experiments, 
                    potential=chosen_potential, 
                    index=current_index
                )        
                
                # Rysujemy proste dopasowania CDL na prawej połówce DoubleLayerCanvas
                self.canvas.plot_cdl_fit(sample.short_name, results_dict, color=self.cmap(i))

                # Tworzymy obiekt analizy (np. do zapisu w historii)
                x = DoubleLayerAnalysis(
                    name=sample.sample_name, 
                    cycle=cycle_num,
                    experiments=experiments,
                    fitting_data=results_dict['df_fitting'],
                    raw_data=results_dict['df_data'],
                    potential=chosen_potential
                )