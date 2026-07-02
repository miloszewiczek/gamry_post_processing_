from contextlib import contextmanager
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QPushButton, QComboBox, QLabel, QGroupBox, QWidget, QSplitter
from PyQt5.QtCore import Qt, pyqtSignal
from core.experiments import Voltammetry, ECSA
from gui_PtQt.small_widgets import TreeSelectorWithCheckboxes, SimpleDoubleSpinBox, Selector, SelectorWithSample
from gui_PtQt.plotting_area import DoubleLayerCanvas
from core.functions.functions import calculate_ECSA_from_slope
import matplotlib.cm as cm
from core import ExperimentManager, analysis_manager
from core.experiments.analysis import DoubleLayerAnalysis
from gui_PtQt.tafel import TafelCoreWidget
import pandas as pd


class DoubleLayerDialog(QDialog):
    """Tradycyjne okno z drzewem wyboru dla użytkownika."""
    def __init__(self, selected_indices, manager=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Double Layer Capacity & ECSA Calculation")
        self.resize(1500, 700) # Nieco wyższe okno, aby zmieścić Tracker pod spinboxami
        
        # Komponenty
        self.selector = SelectorWithSample(selected_indices)
        self.analysis_widget = DoubleLayerCoreWidget(manager=manager)
        self.analysis_widget.analysis_done.connect(self.selector.mark_as_analyzed)
        
        # Główny layout okna
        main_layout = QHBoxLayout(self)
        
        # Tworzymy widget-kontener dla lewego panelu (Selektora)
        left_widget = QWidget()
        left_panel = QVBoxLayout(left_widget)
        left_panel.setContentsMargins(0, 0, 0, 0) # Kasujemy marginesy wewnętrzne
        left_panel.addWidget(QLabel("<b>Select Experiments:</b>"))
        left_panel.addWidget(self.selector)
        
        # Wykorzystujemy QSplitter zamiast sztywnych stretchów w layoucie
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(self.analysis_widget)
        
        # Ustawiamy proporcje startowe: Selektor (np. 400px), Rdzeń analizy (np. 900px)
        splitter.setSizes([400, 900])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(splitter)
        
        # Łączenie sygnałów
        self.selector.flat_list_signal.connect(self.analysis_widget.set_experiments)
        self.selector.flat_list_signal.connect(self.analysis_widget.enable_next_analysis)

class DoubleLayerCoreWidget(TafelCoreWidget):
    """
    Serce analizy. Nie posiada selektora danych. 
    Wymaga podania gotowego słownika z eksperymentami przez metodę 'set_experiments'.
    """
    analysis_done = pyqtSignal()

    def __init__(self, manager: ExperimentManager, parent=None):
        # 1. Wywołujemy konstruktor bazy z odpowiednim Canvasem
        # Konstruktor bazy na końcu wywoła setup_ui(), który w tym przypadku
        # zostanie uruchomiony z TEJ klasy (polimorfizm).
        super().__init__(manager, parent, canvas_type=DoubleLayerCanvas)
        
        # 2. Nadpisujemy specyficzne zmienne dla CDL
        self.default_analysis_prefix = 'CDL'
        self.cmap = None
        self.experiment_dict = {}
        self.fitting_data_list = []
        self.raw_data_list = []
        self.previous_selection = None

    def setup_ui(self):

        from .small_widgets import Tracker
        from PyQt5.QtWidgets import QFormLayout, QSplitter

        # Inicjalizacja Tracker
        self.track = Tracker(column_names=['Name','Potential', 'Curve'],
                             column_widths=[50,50,50],
                             add_delete=True)

        # Kontrolki specyficzne dla CDL
        self.potential_spinbox = SimpleDoubleSpinBox(0, None)
        self.curve_combobox = QComboBox()
        self.calculate_btn = QPushButton("Calculate CDL")
        self.add_analysis_btn = QPushButton('Add to Table')
        self.save_analysis_btn = QPushButton('Save Final Analysis')
        
        # Wizualne wyróżnienie głównego przycisku kalkulacji
        self.calculate_btn.setStyleSheet("font-weight: bold; padding: 5px;")
        self.save_analysis_btn.setStyleSheet("background-color: #2a75ad; color: white; font-weight: bold; padding: 5px;")

        # Łączymy sygnały
        self.connect_signals()

        # Główny układ widżetu
        main_layout = QHBoxLayout(self)
        
        # --- LEWY PANEL KONTROLNY ---
        control_widget = QWidget()
        control_layout = QVBoxLayout(control_widget)
        control_layout.setContentsMargins(0, 0, 0, 0)
        
        settings_group = QGroupBox("Plotting & Analysis Settings")
        # Zapobiega nadmiernemu rozpychaniu panelu kontrolnego w poziomie
        settings_group.setMaximumWidth(320) 
        
        # Organizacja parametrów w układzie formularza (etykieta po lewej, pole po prawej)
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignLeft)
        form_layout.addRow(QLabel("Curve Index:"), self.curve_combobox)
        form_layout.addRow(QLabel("Potential [V]:"), self.potential_spinbox)
        
        # Układ przycisków
        settings_layout = QVBoxLayout(settings_group)
        settings_layout.addLayout(form_layout)
        settings_layout.addSpacing(10)
        settings_layout.addWidget(self.calculate_btn)
        settings_layout.addWidget(self.add_analysis_btn)
        
        # Linia oddzielająca sekcję tabeli/zapisu
        settings_layout.addSpacing(15)
        settings_layout.addWidget(QLabel("<b>Saved Points Tracker:</b>"))
        settings_layout.addWidget(self.track)
        
        settings_layout.addSpacing(10)
        settings_layout.addWidget(self.save_analysis_btn)
        
        self.save_analysis_btn.clicked.connect(self.create_analysis)
        
        control_layout.addWidget(settings_group)
        control_layout.addStretch() # Spycha całą zawartość grupy do góry, zapobiegając rozstrzeleniu widżetów w pionie

        # --- PRAWY PANEL (WYKRES) ---
        canvas_widget = QWidget()
        canvas_layout = QVBoxLayout(canvas_widget)
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        canvas_layout.addWidget(self.canvas)
        canvas_layout.addWidget(self.canvas.toolbar)

        # Wewnętrzny splitter dla panelu kontrolnego i wykresu
        internal_splitter = QSplitter(Qt.Horizontal)
        internal_splitter.addWidget(control_widget)
        internal_splitter.addWidget(canvas_widget)
        internal_splitter.setSizes([320, 800]) # Sztywne 320px na opcje, reszta na wykres
        internal_splitter.setCollapsible(0, False) # Blokada przed całkowitym schowaniem opcji
        
        main_layout.addWidget(internal_splitter)

    def connect_signals(self):
        self.curve_combobox.currentIndexChanged.connect(self.replot_selected_curve)
        self.curve_combobox.currentIndexChanged.connect(self.enable_next_analysis)

        self.calculate_btn.clicked.connect(self.run_cdl_calculation)
        self.potential_spinbox.valueChanged.connect(self.canvas.move_vline)
        self.potential_spinbox.valueChanged.connect(self.enable_next_analysis)
        self.add_analysis_btn.clicked.connect(self.add_data)

    @contextmanager
    def signals_blocked(self, widget):
        """Bezpieczny menedżer kontekstu do blokowania sygnałów."""
        widget.blockSignals(True)
        try:
            yield
        finally:
            widget.blockSignals(False)

    def enable_next_analysis(self):
        self.calculate_btn.setEnabled(True)

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
                
                self.previous_selection = self.curve_combobox.currentText()
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
        
        with self.signals_blocked(self.curve_combobox):
            self.curve_combobox.clear()
            self.curve_combobox.addItems(available_curves)

            if self.previous_selection in available_curves:
                self.curve_combobox.setCurrentText(self.previous_selection)
            elif available_curves:
                current_max_item = self.curve_combobox.count()
                self.curve_combobox.setCurrentIndex(current_max_item - 1)
                
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

                mi_tuple = (sample.user_tag, sample.sample_name, cycle_num)

                multi_index_tuples.append(mi_tuple)
                fitting_data.append(results_dict['df_fitting'])
                data.append(results_dict['df_data'])
        
        names = ('Tag', 'Sample', 'Cycle')
        self.fitting_data = pd.concat(fitting_data, axis = 0)
        multiindex = pd.MultiIndex.from_tuples(multi_index_tuples, names = names)
        self.fitting_data.index = multiindex


        self.raw_data = pd.concat(data, axis = 1, keys = multi_index_tuples, names = names)

        self.calculate_btn.setDisabled(True)
        self.add_analysis_btn.setEnabled(True)

    def add_data(self):
        if hasattr(self, 'fitting_data'):
            self.fitting_data_list.append(self.fitting_data)
            self.raw_data_list.append(self.raw_data)

            data_to_store = (self.raw_data, self.fitting_data)

            columns = ['Test', 
                    str(self.potential_spinbox.value()),
                    self.curve_combobox.currentText()]
            self.track.add_row(columns = columns, data = data_to_store)
            self.add_analysis_btn.setDisabled(True)
            
            self.analysis_done.emit()
        

    def join_data(self, data: list[pd.DataFrame], axis = 0):
        if data is not None:
            joined_data = pd.concat(data, axis = axis)
            return joined_data

    def create_analysis(self):
        raw_data, fitting_data = self.track.get_data() # first is raw_data, second is fiting data

        if raw_data and fitting_data:
            name = analysis_manager.ask_for_analysis_name(self.default_analysis_prefix)
            if name:
                
                joined_raw_data = self.join_data(raw_data, axis = 1)
                joined_fitting_data = self.join_data(fitting_data, axis = 0)
                
                cdl_analysis = DoubleLayerAnalysis(
                                                    name=name, 
                                                    experiments=self.experiments,
                                                    raw_data=joined_raw_data,
                                                    fitting_data=joined_fitting_data,
                                                    )   
                analysis_manager.add_analysis(cdl_analysis)
        