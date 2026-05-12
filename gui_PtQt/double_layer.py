from gui.small_widgets import Selector, SimpleDoubleSpinBox
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QPushButton, QDialog, QComboBox
from gui_PtQt.plotting_area import PlottingCanvas
from PyQt5.QtCore import Qt
from functions.functions import calculate_ECSA_from_slope


class DoubleLayer(QDialog):
    def __init__(self, items):
        super().__init__()

        for item in items:
            experiment = item.data(Qt.UserRole)
            if hasattr(experiment, "data_list") and hasattr(experiment, "processed_data"):
                continue
            else:
                experiment.load_all()
                experiment.process_data()

        self.selector = Selector(items)
        self.canvas = PlottingCanvas()
        self.init_gui()
        self.selector.item_changed.connect(self.update_plot)

    def init_gui(self):
        
        layout = QVBoxLayout()

        self.potential_double_box = SimpleDoubleSpinBox(0, None)
        self.calculate_btn = QPushButton(text = 'Calculate CDL')
        self.calculate_btn.clicked.connect(self.calculate_cdl)
        self.curve_index_checkbox = QComboBox()

        layout.addWidget(self.selector)
        layout.addWidget(self.canvas)
        layout.addWidget(self.potential_double_box)
        layout.addWidget(self.calculate_btn)
        layout.addWidget(self.curve_index_checkbox)

        self.setLayout(layout)

    def update_plot(self):
        self.experiments = self.selector.get_experiments_to_analysis()
        maximum_len = [(len(experiment.data_list)) for experiment in self.experiments]
        maximum_len = min(maximum_len)
        maximum_len = list(range(maximum_len))
        maximum_len = [str(max_len) for max_len in maximum_len]
        self.curve_index_checkbox.addItems(maximum_len)

        # self.canvas.plot_experiments_no_color(self.experiments)

    def calculate_cdl(self):
        if self.experiments:
            values = [self.potential_double_box.value()]
            indexes = [0,]

            x = calculate_ECSA_from_slope(self.experiments, values, indexes)


    



    