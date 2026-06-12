from contextlib import contextmanager
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QPushButton, QComboBox, QLabel, QGroupBox, QWidget
from PyQt5.QtCore import Qt
from core.experiments import Voltammetry, ECSA
from gui_PtQt.small_widgets import TreeSelectorWithCheckboxes, SimpleDoubleSpinBox, Selector, SelectorWithSample
from gui_PtQt.plotting_area import DoubleLayerCanvas
from core.functions.functions import calculate_ECSA_from_slope
import matplotlib.cm as cm
from core import ExperimentManager, analysis_manager
from core.experiments.analysis import DoubleLayerAnalysis
from gui_PtQt.tafel import TafelCoreWidget


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
        self.selector.flat_list_signal.connect(self.analysis_widget.set_experiments)
        

class DoubleLayerCoreWidget(TafelCoreWidget):
    """
    Serce analizy. Nie posiada selektora danych. 
    Wymaga podania gotowego słownika z eksperymentami przez metodę 'set_experiments'.
    """

    def __init__(self, manager: ExperimentManager, parent=None):
        # 1. Wywołujemy konstruktor bazy z odpowiednim Canvasem
        # Konstruktor bazy na końcu wywoła setup_ui(), który w tym przypadku
        # zostanie uruchomiony z TEJ klasy (polimorfizm).
        super().__init__(manager, parent, canvas_type=DoubleLayerCanvas)
        
        # 2. Nadpisujemy specyficzne zmienne dla CDL
        self.default_analysis_prefix = 'CDL'
        self.cmap = None
        self.experiment_dict = {}

    def setup_ui(self):
        """Nadpisujemy całkowicie wygląd widżetu bazowego."""
        # Inicjalizacja kontrolek specyficznych TYLKO dla CDL
        self.potential_spinbox = SimpleDoubleSpinBox(0, None)
        self.curve_combobox = QComboBox()
        self.calculate_btn = QPushButton("Calculate CDL")
        self.save_analysis_btn = QPushButton('Save analysis')

        # Łączymy sygnały
        self.connect_signals()

        # Budujemy nowy układ (HBoxLayout zamiast bazowego VBoxLayout)
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
        
        self.save_analysis_btn.clicked.connect(self.create_analysis)
        settings_layout.addWidget(self.save_analysis_btn)

        control_layout.addWidget(settings_group)
        control_layout.addStretch()
        
        # Kompozycja główna: Panel kontrolny po lewej, wykres po prawej
        canvas_layout = QVBoxLayout()
        canvas_layout.addWidget(self.canvas)
        canvas_layout.addWidget(self.canvas.toolbar)

        main_layout.addLayout(control_layout, stretch=1)
        main_layout.addLayout(canvas_layout, stretch=3)
        
        # Ponieważ w bazie i w potomku bazujemy na self.canvas, 
        # toolbar i plot_btn z bazy po prostu "wiszą" w próżni i nie są wyświetlane.

    def connect_signals(self):
        self.curve_combobox.currentIndexChanged.connect(self.replot_selected_curve)
        self.calculate_btn.clicked.connect(self.run_cdl_calculation)
        self.potential_spinbox.valueChanged.connect(self.canvas.move_vline)

    @contextmanager
    def signals_blocked(self, widget):
        """Bezpieczny menedżer kontekstu do blokowania sygnałów."""
        widget.blockSignals(True)
        try:
            yield
        finally:
            widget.blockSignals(False)

    def connect_signals(self):
        self.curve_combobox.currentIndexChanged.connect(self.replot_selected_curve)
        self.calculate_btn.clicked.connect(self.run_cdl_calculation)
        self.potential_spinbox.valueChanged.connect(self.canvas.move_vline)

    def set_experiments(self, experiments):
        self.experiments = experiments
        self.experiment_dict = self.manager.construct_tree_with_cycles(experiments)
        
        # Dynamiczne ustawienie colormapy na bazie wstrzykniętych danych
        num_samples = len(self.experiment_dict.keys())
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
                
        self.replot_selected_curve()
        
        # AUTOMATYKA: Bezpieczne ustawienie spinboxa bez wywoływania przedwczesnych sygnałów rysowania
        if hasattr(self.experiments[0], 'get_half_potential'):
            x = self.experiments[0].get_half_potential()
            with self.signals_blocked(self.potential_spinbox):
                self.potential_spinbox.setValue(x)
            # Ręcznie przesuwamy kreskę na wykresie po bezpiecznej zmianie wartości
            self.canvas.move_vline(x)

    def replot_selected_curve(self):
        """Odświeża tylko lewy wykres (Krzywe CV)."""
        self.canvas.clear_except_line()

        raw_text = self.curve_combobox.currentText()
        if raw_text and raw_text.isdigit() and self.experiment_dict:
            selected_curve = [int(raw_text)]
            
            for sample, cycle_dict in self.experiment_dict.items():
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

        multi_index_tuples = []
        fitting_data = []
        data = []
        
        import pandas as pd

        new_dict = {}
        for sample, cycle_dict in self.experiment_dict.items():
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


                mi_tuple = (sample.sample_name, cycle_num, chosen_potential)

                multi_index_tuples.append(mi_tuple)
                fitting_data.append(results_dict['df_fitting'])
                data.append(results_dict['df_data'])
        
        names = ('Sample', 'Cycle', 'Potential [V]')
        self.fitting_data = pd.concat(fitting_data, axis = 0, keys = multi_index_tuples, names = names)
        self.raw_data = pd.concat(data, axis = 1, keys = multi_index_tuples, names = names)

    def keyPressEvent():
        pass
    
    def create_analysis(self):

        name = self.ask_for_analysis_name()
        if (name) and (hasattr(self, 'fitting_data')): # it only exists once we make a CDL_calculation!
            cdl_analysis = DoubleLayerAnalysis(
                                                name=name, 
                                                experiments=self.experiments,
                                                fitting_data=self.fitting_data,
                                                raw_data=self.raw_data,
                                                )   
            analysis_manager.add_analysis(cdl_analysis)