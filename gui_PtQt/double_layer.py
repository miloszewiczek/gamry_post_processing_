from gui.small_widgets import Selector, SimpleDoubleSpinBox
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QPushButton, QDialog
from gui_PtQt.plotting_area import PlottingCanvas
from functions.functions import calculate_ECSA_from_slope


class DoubleLayer(QDialog):
    def __init__(self, items):
        super().__init__()

        self.selector = Selector(items)
        self.canvas = PlottingCanvas()
        self.init_gui()
        self.selector.item_changed.connect(self.update_plot)

    def init_gui(self):
        
        layout = QVBoxLayout()

        self.potential_double_box = SimpleDoubleSpinBox(0, None)
        self.calculate_btn = QPushButton(text = 'Calculate CDL')
        self.calculate_btn.clicked.connect(self.calculate_cdl)

        layout.addWidget(self.selector)
        layout.addWidget(self.canvas)
        layout.addWidget(self.potential_double_box)
        layout.addWidget(self.calculate_btn)



        self.setLayout(layout)

    def update_plot(self):
        self.experiments = self.selector.get_experiments_to_analysis()
        self.canvas.plot_experiments_no_color(self.experiments)

    def calculate_cdl(self):
        if self.experiments:
            values = [self.potential_double_box.value()]
            indexes = [0,]

            x = calculate_ECSA_from_slope(self.experiments, values, indexes)
            print(x)

    



    