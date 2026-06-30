from PyQt5.QtWidgets import QWidget, QToolBar, QStatusBar
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

class MainToolbar(QToolBar):
    def __init__(self, title, parent = None):
        super().__init__(title, parent)
        self.setMovable(True)


