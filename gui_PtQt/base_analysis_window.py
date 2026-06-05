from PyQt5.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QPushButton, QMessageBox
from PyQt5.QtCore import Qt
from gui.small_widgets import SelectorWithSample
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

class BaseAnalysisWindow(QDialog):
    def __init__(self, selected_indices, parent=None, manager=None):
        super().__init__(parent)
        self.setWindowTitle("Analysis Window")
        self.resize(1400, 600)
        self.manager = manager
        
        # 1. Metoda do nadpisania w klasach potomnych (ładowanie specyficznych danych)
        self._bootstrap_data(selected_indices)
        
        self.selector = SelectorWithSample(selected_indices)
        
        # 2. Dynamiczne przypisanie Canvasu (musi być zdefiniowane w klasie potomnej!)
        self.canvas = self.create_canvas() 
        
        self.plot_btn = QPushButton('Start Analysis Queue')
        self.plot_btn.clicked.connect(self.start_analysis_queue)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        self.experiment_queue = []
        self.current_exp_index = 0
        self.analysis_results = {}

        self.build_ui()

    def create_canvas(self):
        """Metoda abstrakcyjna. Musi zwrócić obiekt Canvasu w klasie potomnej."""
        raise NotImplementedError("Musisz zaimplementować metodę create_canvas()!")

    def build_ui(self):
        main_layout = QHBoxLayout()
        config_layout = QVBoxLayout()
        config_layout.addWidget(self.selector, stretch=2)
        config_layout.addWidget(self.plot_btn)
        main_layout.addLayout(config_layout)
        
        plot_layout = QVBoxLayout()
        plot_layout.addWidget(self.toolbar)
        plot_layout.addWidget(self.canvas)
        main_layout.addLayout(plot_layout, stretch=3)
        self.setLayout(main_layout)
    
    
    def _bootstrap_data(self, selected_indices, analysis_object_type):
        """Wstępne ładowanie i procesowanie danych na bazie zaznaczonych indeksów."""
        for sample, experiments in selected_indices.items():
            for experiment in experiments:
                if isinstance(experiment, analysis_object_type):
                    if not hasattr(experiment, "data_list"):
                        experiment.load_all()
                    if not hasattr(experiment, 'processed_data'):
                        experiment.process_data()

    def start_analysis_queue(self):
        experiments = self.selector.get_flat_list()
        experiments_dict = self.manager.construct_tree_with_cycles(experiments)
        
        self.experiment_queue = []
        for sample, cycle_dict in experiments_dict.items():
            for cycle_num, exps in cycle_dict.items():
                for exp in exps:
                    self.experiment_queue.append((sample, cycle_num, exp))
        
        if not self.experiment_queue:
            QMessageBox.warning(self, "Brak danych", "Kolejka eksperymentów jest pusta!")
            return
            
        self.current_exp_index = 0
        self.load_current_experiment()

    def load_current_experiment(self):
        if self.current_exp_index >= len(self.experiment_queue):
            QMessageBox.information(self, "Koniec", "Przeanalizowano wszystkie próbki z kolejki!")
            return

        sample, cycle_num, exp = self.experiment_queue[self.current_exp_index]
        self.setWindowTitle(f"Analysis - [{sample.sample_name}] Cykl {cycle_num} ({self.current_exp_index + 1}/{len(self.experiment_queue)})")
        
        # Wywołujemy metody implementowane lokalnie w klasach potomnych
        self.get_data_from_experiment(exp)
        self.plot_on_canvas()
        self.setFocus()

    def get_data_from_experiment(self, experiment):
        raise NotImplementedError("Zaimplementuj pobieranie danych!")

    def plot_on_canvas(self):
        raise NotImplementedError("Zaimplementuj rysowanie na swoim specyficznym canvasie!")

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if not self.experiment_queue:
                event.ignore()
                return

            if not self.canvas.hasResult:
                QMessageBox.warning(self, "Brak zaznaczenia", "Select a point and press <Enter>!")
                return

            # Tutaj wykonuje się specyficzna akcja na Enter (np. zapis slope lub cokolwiek)
            self.on_enter_pressed()

            self.current_exp_index += 1
            self.load_current_experiment()
            self.get_data()
            event.accept()

        elif event.key() == Qt.Key_Escape:
            reply = QMessageBox.question(self, 'Wyjście', "Czy przerwać analizę?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes: self.reject()
            else: event.ignore()
        else:
            super().keyPressEvent(event)

    def get_data(self):
        raise NotImplementedError("Zaimplementuj rysowanie na swoim specyficznym canvasie!")

    def on_enter_pressed(self):
        """Opcjonalna metoda do zapisu danych po kliknięciu Enter w klasie potomnej."""
        pass

