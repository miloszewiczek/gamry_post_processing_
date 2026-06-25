from PyQt5.QtWidgets import QFileDialog, QComboBox
from PyQt5.QtCore import Qt
from pathlib import Path
from core import ExperimentLoader, ExperimentManager
import platform
import subprocess
import os

def load_folder(parent = None): 
        folder = QFileDialog.getExistingDirectory(
            parent,
            "Choose Folder",
            ""
        )
        normalized_folder_path = Path(folder)
        files = normalized_folder_path.glob('*.DTA')
        return files

def load_files(parent = None, caption = 'Choose files', directory = "", filter = "Gamry files (*.DTA);;All files (*)"):

    files, _ = QFileDialog.getOpenFileNames(
        parent,
        caption,
        directory,
        filter
    )
    return files

def load_data(parent, files):

    for file in files:
        try:
            # providing manager in create_experiment automatically updates the manager's dict_of_experiments
            experiment = parent.loader.create_experiment(str(file))
            parent.manager.add_experiment(experiment)
            parent.add_experiment_to_model(experiment)

        except Exception as e:
            pass

def shorten_path(path, max_len=30):
    if len(path) <= max_len:
        return path
    return path[:10] + "..." + path[-15:]


def add_category(combo: QComboBox, text):
    """A function dedicated for combobox widgets.
    Adding a nonclickable segment to divide the combobox into groups."""

    combo.addItem(text)
    index = combo.count() - 1
    # Pobieramy model elementu
    item = combo.model().item(index)
    
    # Stylizacja: pogrubienie
    font = item.font()
    font.setBold(True)
    item.setFont(font)
    
    # Blokada: element staje się nieklikalny (szary)
    item.setFlags(item.flags() & ~Qt.ItemIsEnabled)

    combo.insertSeparator(index + 1)


def open_file_in_system_editor(path):
    
    if platform.system() == 'Windows':
        os.startfile(path)
    elif platform.system() == 'Darwin':  # macOS
        subprocess.call(['open', path])
    else:  # Linux
        subprocess.call(['xdg-open', path])

def open_folder_in_explorer(file_path):
    # 1. Upewniamy się, że mamy ścieżkę do folderu
    # Jeśli podano plik, bierzemy jego folder nadrzędny (.parent)
    path = Path(file_path)
    folder_path = str(path.parent if path.is_file() else path)

    # 2. Wywołujemy odpowiednią komendę systemową
    open_file_in_system_editor(folder_path)