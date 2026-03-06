from core import ExperimentLoader, ExperimentManager
from gui_PtQt.loading_bar import ExperimentPanel
from experiments import *
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
from sys import argv

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.loader = ExperimentLoader()
        self.manager = ExperimentManager(self.loader.load_testing(5))
        # delete later
        

        self.setWindowTitle('Milosz PyQt App!')
        self.setMinimumHeight(500)
        self.setMinimumWidth(500)

        self.tree = ExperimentPanel(self.loader, self.manager)
        self.setCentralWidget(self.tree)

if __name__ == '__main__':

    app = QApplication(argv)
    mainwindow = MainWindow()
    mainwindow.show()
    app.exec_()



