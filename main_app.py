from core import ExperimentLoader, ExperimentManager, analysis_manager
from gui_PtQt.loading_bar import ExperimentPanel
from gui_PtQt.plotting_area import PlottingArea, PlotManagerPanel
from core.experiments import *
from PyQt5.Qt import QApplication, QMainWindow, QWidget, QHBoxLayout, QSplitter
from PyQt5.QtCore import Qt, QCoreApplication
from sys import argv
from gui_PtQt.configuration.config import defaults
from core import AnalysisWindow
from PyQt5.QtWidgets import QAction, QMenu, QMenuBar

# Ustawiamy metadane aplikacji raz na samym początku



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

      
        self.loader = ExperimentLoader()
        # self.manager = ExperimentManager(self.loader.load_testing(5))
        self.manager = ExperimentManager()        

        self.analysis_manager = analysis_manager

        self.setWindowTitle('Milosz PyQt App!')
        self.setMinimumHeight(500)
        self.setMinimumWidth(500)

        tmp_Qwidget = QWidget()
        myLayout = QHBoxLayout()
        splitter = QSplitter(Qt.Orientation.Horizontal)
        

        self.experiment_panel = ExperimentPanel(self.loader, self.manager)
        self.analysis_window = AnalysisWindow()

        self.draw_panel = PlottingArea()
        self.plot_manager = PlotManagerPanel()
        self.experiment_panel.plotRequested.connect(self.plot_manager.add_plots)
        self.plot_manager.plotsUpdated.connect(self.draw_panel.Canvas.plot_experiments)
        
        splitter.addWidget(self.experiment_panel)
        splitter.addWidget(self.draw_panel)
        splitter.addWidget(self.plot_manager)
        splitter.addWidget(self.analysis_window)

        myLayout.addWidget(splitter)
        tmp_Qwidget.setLayout(myLayout)
        self.setCentralWidget(tmp_Qwidget)

        self._createActions()
        self._createMenuBar()


        # for testing
        for sample in self.manager.samples.values():
            self.experiment_panel.refresh_sample_in_model(sample)

        self.draw_panel.btn.clicked.connect(self.handle_plotting)

    def handle_plotting(self):
        current_exps = self.experiment_panel.get_selected_experiments()
        if current_exps:
            self.plot_manager.add_plots(current_exps)


    def _createActions(self):
        
        # File
        self.loadfilesAction = QAction(self)
        self.loadfilesAction.setText("&Load Files...")
        self.loadfolderAction = QAction(self)
        self.loadfolderAction.setText("Load &Folder...")
        self.deletefileAction = QAction(self)
        self.deletefileAction.setText("&Delete")
        self.copyfileAction = QAction(self)
        self.copyfileAction.setText("&Copy")
        self.exitAction = QAction(self)
        self.exitAction.setText("&Exit")

        self.fileActions = [self.loadfilesAction,
                            self.loadfolderAction,
                            self.deletefileAction,
                            self.copyfileAction,
                            self.exitAction]

        # Selction
        self.selectFiles = QAction(self)
        self.selectFiles.setText("Select all &Files")
        self.selectSamples = QAction(self)
        self.selectSamples.setText("Select all &Samples")
        self.toggleExpand = QAction(self)
        self.toggleExpand.setText("&Expand/Collapse all")

        self.selectActions = [self.selectFiles,
                              self.selectSamples,
                              self.toggleExpand]

        # Analysis
        self.cdlAnalysis = QAction(self)
        self.cdlAnalysis.setText("&Double Layer Capacitance")
        self.tafelAnalysis = QAction(self)
        self.tafelAnalysis.setText("&Tafel analysis")
        self.chronopointAnalysis = QAction(self)
        self.chronopointAnalysis.setText("&Chronoamperometry analysis")
        self.overpotentialAnalysis = QAction(self)
        self.overpotentialAnalysis.setText("&Overpotentials")

        self.analysisActions = [self.cdlAnalysis,
                                self.tafelAnalysis,
                                self.chronopointAnalysis,
                                self.overpotentialAnalysis]

    def _createMenuBar(self):
        
        # Getting menuBar
        menuBar = self.menuBar()

        # File menu
        filemenu = QMenu("&File", self)
        filemenu.addActions(self.fileActions) # Adding file actions
        menuBar.addMenu(filemenu)
        
        # Select menu
        selectmenu = QMenu("&Select", self)
        selectmenu.addActions(self.selectActions)
        menuBar.addMenu(selectmenu)

        # Analysis menu
        analysis_menu = QMenu("&Analysis", self)
        analysis_menu.addActions(self.analysisActions)
        menuBar.addMenu(analysis_menu)



if __name__ == '__main__':

    QCoreApplication.setOrganizationName("MyChemistryLab")
    QCoreApplication.setApplicationName("ElectrodeAnalyzer")

    defaults = defaults
    app = QApplication(argv)
    mainwindow = MainWindow()
    mainwindow.show()
    app.exec_()



