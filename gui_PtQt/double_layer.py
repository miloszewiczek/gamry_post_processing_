from contextlib import contextmanager
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QPushButton, QComboBox, QLabel, QGroupBox
from PyQt5.QtCore import Qt
from experiments import Voltammetry, ECSA
from gui.small_widgets import TreeSelectorWithCheckboxes, SimpleDoubleSpinBox, Selector
from gui_PtQt.plotting_area import DoubleLayerCanvas
from functions.functions import calculate_ECSA_from_slope


class DoubleLayer(QDialog):
    def __init__(self, source_model, selected_indices, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Double Layer Capacity & ECSA Calculation")
        self.resize(1100, 600)  # Szeroki, panoramiczny layout pod dwa wykresy i drzewo
        
        self.experiments = []
        
        # 1. Wstępne ładowanie i procesowanie surowych danych (Bootstrap)
        self._bootstrap_data(source_model, selected_indices)
        
        # 2. Inicjalizacja komponentów interfejsu
        # Przekazujemy model nadrzędny i indeksy bezpośrednio do selektora z checkboxami
        self.selector = Selector()
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

    def _bootstrap_data(self, source_model, selected_indices):
        """Wstępne ładowanie i procesowanie danych na bazie zaznaczonych indeksów."""
        for ECSA_experiment in selected_indices.items():
            
            # Jeśli w drzewie zaznaczono bezpośrednio obiekt typu ECSA lub Voltammetry, sprawdzamy go
            if isinstance(ECSA_experiment, (ECSA, Voltammetry)):
                if not (hasattr(ECSA_experiment, "data_list") and hasattr(ECSA_experiment, "processed_data")):
                    ECSA_experiment.load_all()
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
        self.experiments = self.selector.get_experiments_to_analysis()
        
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
        raw_text = self.curve_combobox.currentText()
        if raw_text and raw_text.isdigit() and self.experiments:
            selected_curve = [int(raw_text)]
            self.canvas.plot_cv_curves(self.experiments, curves=selected_curve)

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
            
        chosen_potential = self.potential_spinbox.value()
        current_index = self.get_current_indexes()
        if current_index is None:
            return
        
        # Uruchamiamy poprawioną funkcję matematyczną (z bezpiecznym zerowaniem listy punktów)
        fit_data_1, fit_data_2, results_dfs = calculate_ECSA_from_slope(
            ECSA_experiments=self.experiments, 
            potential_list=[chosen_potential], 
            index=current_index
        )
        
        # Rysujemy proste dopasowania CDL na prawej połówce DoubleLayerCanvas
        self.canvas.plot_cdl_fit(results_dfs)
        
        # Wyświetlenie wyznaczonej pojemności w terminalu diagnostycznym
        slope1, intercept1, r_value1 = fit_data_1
        print(f"Wyznaczona pojemność C_dl (z różnicy prądów): {slope1} F, R^2 = {r_value1**2}")