from PyQt5.QtWidgets import QFileDialog, QComboBox, QListView, QTreeView, QLabel, QListWidget, QWidget, QPushButton, QHBoxLayout, QVBoxLayout
from PyQt5.QtCore import Qt, QDir
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
        files = get_files_from_folder(folder)
        return files

def get_files(path, extensions):
    all_files = []
    for ext in extensions:
        all_files.extend(path.glob(ext))
    return all_files

def get_files_from_folder(folder):
    normalized_folder_path = Path(folder)
    files = get_files(path = normalized_folder_path, extensions = ('*.GSequence', '*.DTA'))
    return files

def load_files(parent = None, caption = 'Choose files', directory = "", filter = "Gamry files (*.DTA *.GSequence);;All files (*)"):

    files, _ = QFileDialog.getOpenFileNames(
        parent,
        caption,
        directory,
        filter
    )
    files = [Path(file) for file in files]
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



class CustomMultiFolderDialog(QFileDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 1. Konfiguracja okna dialogowego
        self.setFileMode(QFileDialog.Directory)
        self.setOption(QFileDialog.DontUseNativeDialog, True)
        self.setFilter(QDir.Dirs | QDir.NoDotAndDotDot)
        self.setLabelText(QFileDialog.Accept, "Accept")
        
        # --- ROZWIĄZANIE PROBLEMU: Włączamy wielokrotne zaznaczanie w lewym panelu ---
        list_view = self.findChild(QListView, "listView")
        if list_view:
            list_view.setSelectionMode(QListView.ExtendedSelection)
            
        tree_view = self.findChild(QTreeView, "treeView")
        if tree_view:
            tree_view.setSelectionMode(QTreeView.ExtendedSelection)
        # ----------------------------------------------------------------------------
        
        # 2. Tworzymy nasze własne widżety
        self.label = QLabel("<b>Chosen folders:</b>")
        self.folder_list = QListWidget()
        
        self.btn_add = QPushButton("Add")
        self.btn_remove = QPushButton("Remove")
        
        self.btn_add.clicked.connect(self.add_current_folder)
        self.btn_remove.clicked.connect(self.remove_selected_folder)
        
        # 3. Układamy nasze przyciski w poziomie
        side_btn_layout = QHBoxLayout()
        side_btn_layout.addWidget(self.btn_add)
        side_btn_layout.addWidget(self.btn_remove)
        
        # 4. Tworzymy panel boczny
        side_panel = QWidget()
        side_layout = QVBoxLayout(side_panel)
        side_layout.addWidget(self.label)
        side_layout.addWidget(self.folder_list)
        side_layout.addLayout(side_btn_layout)
        
        # 5. Pobieramy główny layout QFileDialog i dodajemy nasz panel
        main_layout = self.layout()
        main_layout.addWidget(side_panel, 0, 3, 4, 1)
        
        self.resize(900, 500)

    def add_current_folder(self):
        # Pobieramy WSZYSTKIE foldery, które użytkownik aktualnie zaznaczył (Ctrl / Shift / przeciągnięcie myszą)
        selected_dirs = self.selectedFiles()
        
        if selected_dirs:
            # Pobieramy aktualną listę, aby nie dodawać duplikatów
            existing_items = [self.folder_list.item(i).text() for i in range(self.folder_list.count())]
            
            # Iterujemy po wszystkich podświetlonych folderach
            for path in selected_dirs:
                folder_path = os.path.normpath(path)
                
                if folder_path not in existing_items and os.path.isdir(folder_path):
                    self.folder_list.addItem(folder_path)

    def remove_selected_folder(self):
        current_item = self.folder_list.currentItem()
        if current_item:
            self.folder_list.takeItem(self.folder_list.row(current_item))

    def get_chosen_folders(self):
        """Zwraca listę wszystkich plików ze wszystkich dodanych folderów."""
        folder_paths = []
        for i in range(self.folder_list.count()):
            folder_path = self.folder_list.item(i).text()
            files = get_files_from_folder(folder_path)
            folder_paths += files
        return folder_paths
    
    @staticmethod
    def get_folders(parent=None, title="Choose folders"):
        """Tworzy okno, wyświetla je i od razu zwraca (lista_folderów, status_ok)."""
        dialog = CustomMultiFolderDialog(parent)
        dialog.setWindowTitle(title)
        
        result = dialog.exec_()
        
        folder_paths = dialog.get_chosen_folders()
        is_ok = result == QFileDialog.Accepted
        return folder_paths, is_ok