from PyQt5.QtWidgets import QFileDialog
from pathlib import Path
from core import ExperimentLoader, ExperimentManager

def load_folder(parent = None): 
        folder = QFileDialog.getExistingDirectory(
            parent,
            "Choose Folder",
            ""
        )
        normalized_folder_path = Path(folder)
        files = normalized_folder_path.glob('*.DTA')
        return files

def load_files(parent = None):

    files, _ = QFileDialog.getOpenFileNames(
        parent,
        "Choose files",
        "",
        "Gamry files (*.DTA);;All files (*)"
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