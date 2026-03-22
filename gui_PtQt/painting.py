from PyQt5.QtGui import QPixmap, QColor, QPainter, QIcon
from PyQt5.QtCore import Qt

def create_line_icon(color_hex):
    # Tworzymy obszar roboczy (np. 32x16 px, żeby przypominało linię)
    pixmap = QPixmap(32, 16)
    pixmap.fill(Qt.GlobalColor.transparent) # Przezroczyste tło
    
    painter = QPainter(pixmap)
    # Włączamy antyaliasing, żeby linia była gładka
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # Rysujemy grubą linię na środku
    color = QColor(color_hex)
    painter.setPen(color)
    painter.setBrush(color)
    
    # Rysujemy zaokrąglony prostokąt, który wygląda jak odcinek linii
    painter.drawRoundedRect(2, 6, 28, 4, 2, 2)
    painter.end()
    
    # KLUCZ: Zwracamy QIcon utworzony z Pixmapy
    return QIcon(pixmap)


class ColorManager():
    def __init__(self):

        self.last_used = None
        self.colors = {'List 1': 
                       ['#FF00FF',
                        '#FF0F00',
                        '#00F0FF',
                        '#000000',]}
        
    def get_next_color(self, list):
        
        #first instance or more plots than there are in the color list
        if (self.last_used is None) or (self.last_used is self.colors[list][-1]):
            color = self.colors[list][0]
        else:
            color_index = self.colors[list].index(self.last_used) + 1
            color = self.colors[list][color_index]

        self.last_used = color
        
        return color
    

        
