from core import ExperimentLoader, ExperimentManager, analysis_manager
from gui_PtQt.loading_bar import ExperimentPanel
from gui_PtQt.plotting_area import PlottingArea, PlotManagerPanel
from gui_PtQt.toolbar import MainToolbar
from core.experiments import *
from PyQt5.Qt import QApplication, QMainWindow, QWidget, QHBoxLayout, QSplitter
from PyQt5.QtCore import Qt, QCoreApplication
from sys import argv
from gui_PtQt.configuration.config import defaults
from core import AnalysisWindow
from PyQt5.QtWidgets import QAction, QMenu, QMenuBar

# Ustawiamy metadane aplikacji raz na samym początku



class MainWindow(QMainWindow):
    def __init__(self, args_list):
        super().__init__()

        
        self.loader = ExperimentLoader()
        if ('-testing' in args_list) or ('-t' in args_list):
            self.manager = ExperimentManager(self.loader.load_testing(5))
        else:
            self.manager = ExperimentManager()        


        self.menus = {
            "file": self.menuBar().addMenu("&File"),
            "edit": self.menuBar().addMenu("&Edit"),
            "analysis": self.menuBar().addMenu("&Analysis"),
            "selection": self.menuBar().addMenu("&Selection")
        }

        self.analysis_manager = analysis_manager

        self.setWindowTitle('Milosz PyQt App!')
        self.setMinimumHeight(700)
        self.setMinimumWidth(700)

        tmp_Qwidget = QWidget()
        myLayout = QHBoxLayout()
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        self.experiment_panel = ExperimentPanel(self.loader, self.manager)
        self.analysis_window = AnalysisWindow()
        self.top_toolbar = MainToolbar("Top Toolbar", self)
        self.left_toolbar = MainToolbar("Left Toolbar", self)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.left_toolbar)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.top_toolbar)


        self._feed_interface(self.experiment_panel.get_actions())


        self.draw_panel = PlottingArea()
        self.plot_manager = PlotManagerPanel()
        self.experiment_panel.plotRequested.connect(self.plot_manager.add_plots)
        self.plot_manager.plotsUpdated.connect(self.draw_panel.Canvas.plot_experiments)
        
        splitter.addWidget(self.experiment_panel)
        splitter.addWidget(self.draw_panel)
        splitter.addWidget(self.plot_manager)
        splitter.addWidget(self.analysis_window)

        splitter.setSizes([600, 600, 300, 300])

        myLayout.addWidget(splitter)
        tmp_Qwidget.setLayout(myLayout)
        self.setCentralWidget(tmp_Qwidget)

        # for testing
        for sample in self.manager.samples.values():
            self.experiment_panel.refresh_sample_in_model(sample)

        self.draw_panel.btn.clicked.connect(self.handle_plotting)

    def handle_plotting(self):
        current_exps = self.experiment_panel.get_selected_experiments()
        if current_exps:
            self.plot_manager.add_plots(current_exps)


    def _feed_interface(self, actions: dict[str, list[QAction]]):
        """
        Uniwersalna metoda, która potrafi przyjąć paczkę akcji z DOWOLNEGO widżetu
        i odpowiednio rozlokować je w istniejących już menu i toolbarach.
        """
        for group, act_list in actions.items():
            if not act_list:
                continue
                
            # 1. Doklejamy do odpowiedniego menu (jeśli istnieje)
            if group in self.menus:
                self.menus[group].addActions(act_list)
                
            # 2. Decydujemy na podstawie grupy, na który toolbar to leci
            if group in ["file", "edit"]:
                if self.top_toolbar.actions(): # Jeśli coś już jest, dajemy separator
                    self.top_toolbar.addSeparator()
                self.top_toolbar.addActions(act_list)
                
            elif group == "analysis":
                self.left_toolbar.addActions(act_list)

if __name__ == '__main__':

    QCoreApplication.setOrganizationName("MyChemistryLab")
    QCoreApplication.setApplicationName("ElectrodeAnalyzer")

    app = QApplication(argv)
    mainwindow = MainWindow(argv)
    mainwindow.show()
    app.exec_()



