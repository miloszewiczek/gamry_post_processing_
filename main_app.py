from core import ExperimentLoader, ExperimentManager
from gui_PtQt.loading_bar import ExperimentPanel
from gui_PtQt.plotting_area import PlottingArea, PlotManagerPanel
from experiments import *
from PyQt5.Qt import QApplication, QMainWindow, QWidget, QHBoxLayout, QSplitter
from PyQt5.QtCore import Qt
from sys import argv

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.loader = ExperimentLoader()
        self.manager = ExperimentManager(self.loader.load_testing(5))        

        self.setWindowTitle('Milosz PyQt App!')
        self.setMinimumHeight(500)
        self.setMinimumWidth(500)

        tmp_Qwidget = QWidget()
        myLayout = QHBoxLayout()
        splitter = QSplitter(Qt.Orientation.Horizontal)
        

        self.experiment_panel = ExperimentPanel(self.loader, self.manager)
        self.draw_panel = PlottingArea()
        self.plot_manager = PlotManagerPanel(canvas = self.draw_panel.get_canvas())
        
        splitter.addWidget(self.experiment_panel)
        splitter.addWidget(self.draw_panel)
        splitter.addWidget(self.plot_manager)

        myLayout.addWidget(splitter)
        tmp_Qwidget.setLayout(myLayout)
        self.setCentralWidget(tmp_Qwidget)


        for exp in self.manager.get_all():
            self.experiment_panel.add_experiment_to_model(exp)
            
        #self.experiment_panel.tree_view.selectionModel().selectionChanged.connect(self.on_selection_change)


        self.draw_panel.btn.clicked.connect(self.handle_plotting)

    def handle_plotting(self):
        current_exps = self.experiment_panel.get_selected_experiments()
        self.plot_manager.add_plots(current_exps)



if __name__ == '__main__':

    app = QApplication(argv)
    mainwindow = MainWindow()
    mainwindow.show()
    app.exec_()



