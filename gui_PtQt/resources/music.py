from random import choice
from os import listdir
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QPixmap, QCursor

from pathlib import Path

def get_song():
    # 1. Pobieramy folder, w którym znajduje się TEN konkretny plik ze skryptem
    current_dir = Path(__file__).parent
    
    music_dir = current_dir / "gamry_music"
    songs = [f for f in music_dir.iterdir() if f.is_file()]
    
    if not songs:
        return None # Zabezpieczenie na wypadek pustego folderu
    random_song = choice(songs)
    
    return QUrl.fromLocalFile(str(random_song))


def get_cursor():
    # 1. Wskazujesz plik graficzny
        pixmap = QPixmap(":kursor.png")
        pixmap = pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        custom_cursor = QCursor(pixmap, 0, 0)
        return custom_cursor