import sys
from pathlib import Path
from PyQt5.QtWidgets import (QTreeWidget, QWidget, QLayout, QPushButton, QHBoxLayout, 
                             QVBoxLayout, QTreeView, QFileDialog, QMessageBox, 
                             QAbstractItemView, QDialog, QLabel, 
                             QFormLayout, QDialogButtonBox, QTableView, QAction,
                             QComboBox, QMenu, QTextBrowser, QShortcut, QInputDialog, QDoubleSpinBox, QLineEdit, QHeaderView)
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QColor, QIcon, QKeySequence, QBrush
from PyQt5.QtCore import Qt, QAbstractTableModel, QItemSelection, QItemSelectionModel, QPersistentModelIndex, pyqtSignal, QModelIndex

from core import ExperimentLoader, ExperimentManager, Experiment
from core.functions.gui_functions import open_file_in_system_editor, open_folder_in_explorer, get_files_from_folder
from core.functions.gui_functions import load_data, load_files, load_folder, CustomMultiFolderDialog
from gui_PtQt.calculate_diameter import AreaDialogBox, AreaDialog
from gui_PtQt.configuration.config import icon_path
from core.experiments.sample import Sample
from gui_PtQt.small_widgets import TreeFilterProxyModel
from gui_PtQt.pandas_viewer import DataPreviewDialog
from gui_PtQt.resources import qrc_resources



class ExperimentInfoDialog(QDialog):
    def __init__(self, experiment:Experiment, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Info: {experiment.file_name}")
        self.setMinimumWidth(350)
        self.experiment = experiment

        layout = QVBoxLayout(self)
        
        # FormLayout idealnie nadaje się do par "Etykieta: Wartość"
        form = QFormLayout()
        
        self.experiment.load_meta_data()
        for key, val_tuple in experiment.get_essentials().items():
            val = val_tuple[0]
            form.addRow(f"<b>{key}</b>", QLabel(f"{val}"))
        # form.addRow("<b>Nazwa:</b>", QLabel(experiment.file_name))
        # form.addRow("<b>ID:</b>", QLabel(str(experiment.id)))
        # form.addRow("<b>Folder:</b>", QLabel(experiment.folder))
        # form.addRow("<b>Klasa:</b>", QLabel(experiment.__class__.__name__))
        
        layout.addLayout(form)
        
        # Standardowy przycisk OK

        self.btn_change_class = QPushButton("Show Data")
        self.btn_change_class.clicked.connect(self.show_data)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.addButton(self.btn_change_class, QDialogButtonBox.ButtonRole.ActionRole)

        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    def show_data(self):
        data = DataPreviewDialog(self.experiment)
        data.exec()
    
    def open_with(self):
        open_file_in_system_editor(self.experiment.file_path)




class ExperimentPanel(QWidget):

    itemsExported = pyqtSignal(list)
    plotRequested = pyqtSignal(list)

    def __init__(self, loader: ExperimentLoader, manager: ExperimentManager, parent=None, settings=None):
        super().__init__(parent)

        self.loader = loader
        self.manager = manager
        self.settings = settings
        self.expanded_all = False
        
        # 1. Inicjalizacja Modelu i Widoku
        self.tree_view = QTreeView()
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Experiment', 'Class', 'ID'])

        self.proxy_model = TreeFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)

        self.tree_view.setModel(self.proxy_model)
        header = self.tree_view.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tree_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.open_menu)

        self.search_layout = QHBoxLayout()
        search_label = QLabel('Filter: ')
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type to search")
        self.search_layout.addWidget(search_label)
        self.search_layout.addWidget(self.search_input)


        btn_select_all_shortcut = QShortcut(QKeySequence("Ctrl+A"), self.tree_view)
        btn_select_all_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        btn_select_all_shortcut.activated.connect(self.expand_selection_automatically)

        focus_on_filter_shortcut = QShortcut(QKeySequence("Ctrl+D"), self.tree_view)
        focus_on_filter_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        focus_on_filter_shortcut.activated.connect(self.search_input.setFocus)

        
        treeview_layout = QHBoxLayout()
        treeview_layout.addWidget(self.tree_view)
        
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(self.search_layout)
        main_layout.addLayout(treeview_layout)
        
        # 4. Połączenia Sygnałów UI

        self.search_input.textChanged.connect(self.filter_tree)
        self.tree_view.doubleClicked.connect(self.on_double_clicked)
        
        self._init_actions()


    def _init_actions(self):
        self.action_load_files = QAction(QIcon(":file-load.png"), "&Load Files...", self)
        self.action_load_files.setShortcut("Ctrl+O")
        self.action_load_files.triggered.connect(self.load_files)

        self.action_load_folder = QAction(QIcon(":folder-load.png"), "Load &Folder...", self)
        self.action_load_folder.setShortcut("Ctrl+Shift+O")
        self.action_load_folder.triggered.connect(self.load_folder)

        self.action_delete = QAction(QIcon(":file-delete.png"), "&Delete", self)
        self.action_delete.setShortcut("Delete")
        self.action_delete.triggered.connect(self.delete_selected_items)

        self.action_expand_all = QAction(QIcon(":expand.png"), "&Expand/Collapse all", self)
        self.action_expand_all.setShortcut("Ctrl+E")
        self.action_expand_all.triggered.connect(self.toggle_expand)

        self.action_copy = QAction(QIcon(":file-copy.png"),"&Copy", self)
        self.action_copy.setShortcut("Ctrl+C")
        self.action_copy.triggered.connect(self.copy_selected_items)

        self.action_select_samples = QAction(QIcon(":select-samples.png"), "Select all &Samples", self)
        self.action_select_samples.setShortcut("Ctrl+Shift+S")
        self.action_select_samples.triggered.connect(self.select_all_samples)

        self.action_select_experiments = QAction(QIcon(":select-experiments.png"), "Select all &Experiments", self)
        self.action_select_experiments.setShortcut("Ctrl+Shift+E")
        self.action_select_experiments.triggered.connect(self.select_all_experiments_globally)

        self.action_double_layer = QAction(QIcon(":double_layer_analysis.png"), "Double Layer &Capacitance", self)
        self.action_double_layer.setShortcut("Alt+1")
        self.action_double_layer.triggered.connect(self.double_layer)

        self.action_overpotentials = QAction(QIcon(":overpotential_analysis.png"), "&Overpotentials", self)
        self.action_overpotentials.setShortcut("Alt+2")
        self.action_overpotentials.triggered.connect(self.overpotentials)

        self.action_tafel = QAction(QIcon(":tafel_analysis.png"), "&Tafel analysis", self)
        self.action_tafel.setShortcut("Alt+3")
        self.action_tafel.triggered.connect(self.tafel_analysis)

        self.action_chronopoints = QAction(QIcon(":chronopoint_analysis.png"), "C&hronopoints", self)
        self.action_chronopoints.setShortcut("Alt+4")
        self.action_chronopoints.triggered.connect(self.chronopoint_analysis)

        self.action_set_tag = QAction(QIcon(":tag.png"), "Set &tag", self)
        self.action_set_tag.setShortcut("Ctrl+T")
        self.action_set_tag.triggered.connect(self.set_tag)

        self.action_save_all = QAction(QIcon(":disk.png"), 'Save &All Samples', self)
        self.action_save_all.setShortcut("Ctrl+Shift+S")
        self.action_save_all.triggered.connect(self.save_all)


    def get_actions(self):
        action_dict = {'file': [self.action_load_files, self.action_load_folder, self.action_delete, self.action_copy, self.action_save_all],
                       'edit': [self.action_set_tag],
                       'selection': [self.action_expand_all, self.action_select_samples, self.action_select_experiments],
                       'analysis': [self.action_double_layer, self.action_overpotentials, self.action_tafel, self.action_chronopoints]
        }
        return action_dict
    # =========================================================================
    # TRANSLATOR INDEKSÓW (SERCE ARCHITEKTURY)
    # =========================================================================

    def save_all(self):
        sample_items = self.select_all_samples()
        _, sample_objects, _ = self._get_business_objects_from_selection(sample_items)
        for sample in sample_objects:
            self.manager.batch_process_selected_experiments(experiment_collectible = sample.experiments, 
                                                            save_name = sample.sample_name,
                                                            save_dir = sample.sample_path)

    def set_tag(self):
        _, items, indexes = self._get_business_objects_from_selection()
        user_tag_string, ok = QInputDialog.getText(self, 'Set tag', 'Specify the tag used to combine multiple samples:')
        if user_tag_string and ok:
            try:
                self.manager.apply_parameter(items, 'user_tag', user_tag_string)
                for index in indexes:
                    class_idx = index.siblingAtColumn(1)
                    self.model.setData(class_idx, user_tag_string)
            except:
                return

    def _get_business_objects_from_selection(self, clicked_proxy_index=None) -> tuple[str, list]:
        """
        Pobiera aktualnie zaznaczone wiersze i bezpiecznie tłumaczy je na 
        obiekty domenowe. W przypadku zaznaczenia mieszanego (Sample + Experiment),
        pyta użytkownika za pomocą okna dialogowego, którą grupę chce wybrać.
        """
        selection_model = self.tree_view.selectionModel()
        
        if clicked_proxy_index is not None and not isinstance(clicked_proxy_index, bool):
            if not selection_model.isSelected(clicked_proxy_index):
                proxy_indices = [clicked_proxy_index.siblingAtColumn(0)]
            else:
                proxy_indices = selection_model.selectedRows(0)
        else:
            proxy_indices = selection_model.selectedRows(0)

        if not proxy_indices:
            return "NONE", [], "NONE"

        found_samples = []
        found_experiments = []
        source_indexes = []

        # 1. Segregujemy obiekty z zaznaczenia do odpowiednich list
        for idx in proxy_indices:
            source_index = self.proxy_model.mapToSource(idx)
            source_indexes.append(source_index)

            obj = source_index.data(Qt.UserRole)
            
            if isinstance(obj, Sample):
                if obj not in found_samples:
                    found_samples.append(obj)
            elif isinstance(obj, Experiment):
                if obj not in found_experiments:
                    found_experiments.append(obj)

        # 2. LOGIKA DECYZYJNA:

        # Przypadek A: Zaznaczono wyłącznie próbki (Sample)
        if found_samples and not found_experiments:
            return "SAMPLE", found_samples, source_indexes

        # Przypadek B: Zaznaczono wyłącznie eksperymenty (Experiment)
        if found_experiments and not found_samples:
            return "EXPERIMENT", found_experiments, source_indexes

        # Przypadek C: Zaznaczenie MIESZANE -> Wyświetlamy komunikat dla użytkownika
        if found_samples and found_experiments:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Niejasne zaznaczenie")
            msg_box.setText("Zaznaczono jednocześnie Próbki (Foldery) oraz Eksperymenty (Pliki).\n"
                            "Które obiekty chcesz wziąć pod uwagę?")
            
            # Dodajemy niestandardowe przyciski z rolami
            btn_samples = msg_box.addButton("Tylko Próbki", QMessageBox.ButtonRole.YesRole)
            btn_experiments = msg_box.addButton("Tylko Eksperymenty", QMessageBox.ButtonRole.NoRole)
            btn_cancel = msg_box.addButton("Anuluj", QMessageBox.ButtonRole.RejectRole)
            
            msg_box.exec_()
            
            clicked_btn = msg_box.clickedButton()
            
            if clicked_btn == btn_samples:
                return "SAMPLE", found_samples, source_indexes
            elif clicked_btn == btn_experiments:
                return "EXPERIMENT", found_experiments, source_indexes
            else:
                return "NONE", [], "NONE" # Użytkownik anulował akcję

        return "NONE", [], "NONE"

    # =========================================================================
    # MENU KONTEKSTOWE
    # =========================================================================

    def open_menu(self, position):
        proxy_index = self.tree_view.indexAt(position)
        if not proxy_index.isValid():
            return

        node_type, business_objects, _ = self._get_business_objects_from_selection(proxy_index)
        if node_type == "NONE" or not business_objects:
            return

        menu = QMenu(self)
        if node_type == "SAMPLE":
            self._build_sample_menu(menu, business_objects)
        elif node_type == "EXPERIMENT":
            self._build_experiment_menu(menu, business_objects)

        if not menu.isEmpty():
            menu.exec(self.tree_view.viewport().mapToGlobal(position))

    def _build_sample_menu(self, menu: QMenu, samples: list[Sample]):
        all_experiments = []
        for s in samples:
            all_experiments.extend(s.experiments)

        batch_act = menu.addAction(f"Batch process all in {len(samples)} Sample(s)")
        
        def process_sample_and_ui():
            self._bulk_process(all_experiments)
            # Kolorujemy węzły próbek w modelu źródłowym
            items_to_color = []
            for sample in samples:
                for row in range(self.model.rowCount()):
                    item = self.model.item(row)
                    if item and item.data(Qt.UserRole) == sample:
                        items_to_color.append(item)
            self.color_items(items_to_color, QColor('green'))

        batch_act.triggered.connect(process_sample_and_ui)
        
        menu.addSeparator()
        delete_folder_act = menu.addAction("Delete Selected Sample(s)")
        delete_folder_act.triggered.connect(lambda: self._delete_samples_logic(samples))

        batch_apply_parameters = menu.addAction("Apply parameters to all experiments")
        batch_apply_parameters.triggered.connect(lambda: self._open_area_dialog(all_experiments))

    def _build_experiment_menu(self, menu: QMenu, experiments: list[Experiment]):
        amount = len(experiments)

        info_act = menu.addAction("Show details")
        info_act.setEnabled(amount == 1)
        if amount == 1:
            info_act.triggered.connect(lambda: self._show_experiment_info(experiments[0]))

        note_act = menu.addAction("Open in text editor")
        note_act.triggered.connect(lambda: [open_file_in_system_editor(e.file_path) for e in experiments])

        menu.addSeparator()
        proc_act = menu.addAction("Process")
        proc_act.triggered.connect(lambda: self._bulk_process(experiments))

        param_act = menu.addAction("Set Geometrical Area")
        param_act.triggered.connect(lambda: self._open_area_dialog(experiments))
        
        save_act = menu.addAction('Save to Excel')
        save_act.triggered.connect(lambda: self.quick_save_logic(experiments))

        plot_act = menu.addAction('Plot')
        plot_act.triggered.connect(lambda: self.plotRequested.emit(experiments))


        #testing 
        from gui_PtQt.mean_calculator import MeanCalculator
        mean_act = menu.addAction('Mean')
        mean_act.triggered.connect(lambda: MeanCalculator(self, experiments))

        # --- SEKCOWI DEDYKOWANE (Rozbudowa np. pod ECSA) ---
        ecsa_exps = [e for e in experiments if getattr(e, 'object_type', None) == 'ECSA' or e.__class__.__name__ == 'ECSA']
        if ecsa_exps:
            menu.addSeparator()
            ecsa_menu = menu.addMenu("ECSA Options")
            ecsa_calc_act = ecsa_menu.addAction(f"Calculate ECSA Capacity ({len(ecsa_exps)})")
            ecsa_calc_act.triggered.connect(lambda: print(f"ECSA calculation for {len(ecsa_exps)} objects."))

        eis_exps = [e for e in experiments if getattr(e, 'object_type', None) == 'EIS' or e.__class__.__name__ == 'EIS']
        if eis_exps:
            from core.experiments import EIS
            from gui_PtQt.small_widgets import DataSelector
            eis_exps: list[EIS]
            menu.addSeparator()
            eis_menu = menu.addMenu("EIS Options")
            eis_ru_act = eis_menu.addAction(f"Quick Ru")
            eis_ru_act.triggered.connect(lambda: self.get_and_set_Ru(eis_exps[0]))

            eis_ru_interactive_act = eis_menu.addAction(f"Select Ru Value")
            eis_ru_interactive_act.triggered.connect(lambda x: DataSelector(self.manager, experiments, object_type = EIS, callback = apply))

            def apply(Ru_value):
                sample = self.manager.find_sample(experiments[0])
                for experiment in sample:
                    experiment.set_Ru(Ru_value[0])
                QMessageBox.information(self, 'Ru set', f'Ru was set to {Ru_value[0]} for sample: \n {sample.sample_name}', QMessageBox.Ok)

                
    def get_and_set_Ru(self, selected_experiment = None):
            if selected_experiment:
                Ru_to_set = selected_experiment.get_Ru()
                sample = self.manager.find_sample(selected_experiment)
                for exp in sample:
                    exp.set_Ru(Ru_to_set)
                QMessageBox.information(self, 'Ru set', f'Ru was set to {Ru_to_set} for sample: \n {sample.sample_name}', QMessageBox.Ok)


    def copy_selected_items(self):
        node_type, objects, _ = self._get_business_objects_from_selection()
        if not objects:
            return

        if node_type == "SAMPLE":
            reply = QMessageBox.question(self, 'Copying folder', 'Copy selected folders?', QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                for sample in objects:
                    for experiment in sample.experiments:
                        new_sample, _ = self.manager.copy_experiment(experiment, new_id=self.loader.get_counter(), sample_name=sample.sample_name + "Copy")
                        self.loader.update_counter(1)
                    self.refresh_sample_in_model(new_sample)
        
        elif node_type == "EXPERIMENT":
            for experiment in objects:
                new_experiment = self.manager.copy_experiment(experiment, new_id=self.loader.get_counter())
                self.loader.update_counter(1)
                
                # Znajdź rodzica tego eksperymentu w modelu źródłowym, aby dodać kopię pod niego
                for row in range(self.model.rowCount()):
                    parent_item = self.model.item(row)
                    sample_obj = parent_item.data(Qt.UserRole)
                    if sample_obj and experiment in sample_obj.experiments:
                        self.add_experiment_to_item(parent_item, new_experiment)
                        break

    def delete_selected_items(self, checked_index=None):
        node_type, objects, _ = self._get_business_objects_from_selection(checked_index)
        if not objects:
            if checked_index is None:
                QMessageBox.information(self, 'Select node', 'No node selected...')
            return

        if node_type == "SAMPLE":
            self._delete_samples_logic(objects)
        elif node_type == "EXPERIMENT":
            for exp in objects:
                self.manager.delete_experiment_by_id(exp.id)
                
                # Usuń wiersz bezpośrednio z modelu źródłowego
                for r in range(self.model.rowCount()):
                    parent_item = self.model.item(r)
                    if parent_item:
                        for child_row in range(parent_item.rowCount()):
                            child_item = parent_item.child(child_row, 0)
                            if child_item and child_item.data(Qt.UserRole) == exp:
                                parent_item.removeRow(child_row)
                                # Jeśli rodzic został pusty, usuń go również
                                if parent_item.rowCount() == 0:
                                    self.model.removeRow(r)
                                return

    def _delete_samples_logic(self, samples: list[Sample]):
        reply = QMessageBox.question(self, 'Deleting Folder', f'Delete all {len(samples)} selected samples?', QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            for sample in samples:
                self.manager.delete_sample(sample)
                for row in range(self.model.rowCount()):
                    item = self.model.item(row)
                    if item and item.data(Qt.UserRole) == sample:
                        self.model.removeRow(row)
                        break

    def quick_save_logic(self, experiments: list[Experiment]):
        name, done = QInputDialog.getText(self, 'Save name', 'Enter name of file')
        if done and name:
            self.manager.batch_process_selected_experiments(experiments, name, 'tag')

    def double_layer(self):
        from gui_PtQt.double_layer import DoubleLayerDialog
        # Pobieramy bezpośrednio listę zaznaczonych obiektów eksperymentów
        _, selected_experiments, _ = self._get_business_objects_from_selection()
        filtered = self.manager.filter(selected_experiments, object_type='ECSA')
        sample_experiment_tree = self.manager.construct_tree(filtered)

        x = DoubleLayerDialog(sample_experiment_tree, manager = self.manager)
        if x.exec() == QDialog.accepted:
            print('elo')

    def overpotentials(self):
        from gui_PtQt.overpotentials import OverpotentialsWindow
        _, selected_experiments, _ = self._get_business_objects_from_selection()
        filtered = self.manager.filter(selected_experiments, object_type = 'LinearVoltammetry')
        sample_experiment_tree = self.manager.construct_tree(filtered)
        x = OverpotentialsWindow(sample_experiment_tree, manager = self.manager)
        if x.exec() == QDialog.accepted:
            print('naura')

    def tafel_analysis(self):
        from gui_PtQt.tafel import TafelAnalysisWindow
        _, selected_experiments, _ = self._get_business_objects_from_selection()
        filtered = self.manager.filter(selected_experiments, object_type = 'LinearVoltammetry')
        sample_experiment_tree = self.manager.construct_tree(filtered)
        x = TafelAnalysisWindow(sample_experiment_tree, manager = self.manager)
        if x.exec() == QDialog.accepted:
            print('elo')


    def chronopoint_analysis(self):
        from gui_PtQt.chronopoints import ChronopointsAnalysisWindow
        _, selected_experiments, _ = self._get_business_objects_from_selection()
        filtered = self.manager.filter(selected_experiments, object_type = 'Chronoamperometry')
        sample_experiment_tree = self.manager.construct_tree(filtered)
        x = ChronopointsAnalysisWindow(sample_experiment_tree, manager = self.manager)
        if x.exec() == QDialog.accepted:
            print('elo')

    def on_double_clicked(self, proxy_index):
        if proxy_index.column() != 0:
            proxy_index = proxy_index.siblingAtColumn(0)

        source_index = self.proxy_model.mapToSource(proxy_index)
        identity = source_index.data(Qt.UserRole)

        if isinstance(identity, Experiment):
            self._show_experiment_info(identity)
        elif isinstance(identity, Sample):
            print('DUPA')

    def _show_experiment_info(self, experiment: Experiment):
        dialog = ExperimentInfoDialog(experiment, self)
        dialog.exec()

    def _bulk_process(self, experiments: list[Experiment]):
        for exp in experiments:
            exp.process_data()
        self.tree_view.update()

    def _open_area_dialog(self, experiments: list[Experiment]):
        dialog = AreaDialog(experiments = experiments, manager = self.manager)
        dialog.load_from_settings()

        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            for exp in experiments:
                exp.set_area(data['geometrical_area'])
                exp.set_potential(data['reference_potential'])
                exp.set_Ru(data['Ru'])
                
                # Aktualizacja tooltipa w UI (szukamy odpowiadającego wiersza w modelu źródłowym)
                for row in range(self.model.rowCount()):
                    parent = self.model.item(row)
                    for child_row in range(parent.rowCount()):
                        item = parent.child(child_row, 0)
                        if item and item.data(Qt.UserRole) == exp:
                            item.setToolTip(f"Area: {data['geometrical_area']}")
            dialog.save_to_settings()

    def color_items(self, items: list[QStandardItem], color=None):
        if isinstance(color, QColor):
            for item in items:
                item.setBackground(color)

    # =========================================================================
    # ZAAWANSOWANE OPERACJE NA ZAZNACZENIACH (ZAPOBIEGANIE BŁĘDOM PROXY)
    # =========================================================================

    def select_all_samples(self):
        """Zaznacza absolutnie wszystkie węzły typu Sample na poziomie Proxy."""
        selection_model = self.tree_view.selectionModel()
        root_count = self.proxy_model.rowCount(QModelIndex())
        for row in range(root_count):
            sample_index = self.proxy_model.index(row, 0, QModelIndex())
            selection_model.select(sample_index, QItemSelectionModel.Select | QItemSelectionModel.Rows)

    def select_experiment_siblings(self, experiment_proxy_index: QModelIndex):
        """Zaznacza wszystkie eksperymenty należące do tego samego rodzica na poziomie Proxy."""
        siblings = self.get_siblings(experiment_proxy_index)
        selection_model = self.tree_view.selectionModel()

        for sibling in siblings:
            selection_model.select(sibling, QItemSelectionModel.Select | QItemSelectionModel.Rows)

    def get_siblings(self, experiment_proxy_index):
        """Zaznacza wszystkie eksperymenty należące do tego samego rodzica na poziomie Proxy."""
        parent = experiment_proxy_index.parent()
        siblings = []
        if not parent.isValid():
            return 
        siblings_count = self.proxy_model.rowCount(parent)
        for row in range(siblings_count):
            sibling_index = self.proxy_model.index(row, 0, parent)
            siblings.append(sibling_index)
        return siblings

    def select_all_experiments_globally(self):
        """Przeszukuje całe drzewo proxy i zaznacza każdy eksperyment u każdego rodzica."""
        selection_model = self.tree_view.selectionModel()
        root_count = self.proxy_model.rowCount(QModelIndex())
        for s_row in range(root_count):
            sample_index = self.proxy_model.index(s_row, 0, QModelIndex())
            exp_count = self.proxy_model.rowCount(sample_index)
            for e_row in range(exp_count):
                global_exp_index = self.proxy_model.index(e_row, 0, sample_index)
                selection_model.select(global_exp_index, QItemSelectionModel.Select | QItemSelectionModel.Rows)
        self.tree_view.expandAll()

    def expand_selection_automatically(self):
        """Inteligentny Ctrl+A operujący w całości bezpiecznie na warstwie Proxy."""
        selected = self.tree_view.selectionModel().selectedRows(0)
        if not selected:
            return

        first_index = selected[0]
        if not first_index.parent().isValid():
            self.select_all_samples()
        else:
            parent_proxy_index = first_index.parent()
            local_children_count = self.proxy_model.rowCount(parent_proxy_index)
            if len(selected) >= local_children_count:
                self.select_all_experiments_globally()
            else:
                self.select_experiment_siblings(first_index)

    # =========================================================================
    # POZOSTAŁE METODY POMOCNICZE (WSPARCIE DANYCH)
    # =========================================================================

    def load_folder(self): 
        files, ok = CustomMultiFolderDialog.get_folders(self)
        if files and ok:
            sequence_files = self.load_data(files)
            if sequence_files:
                for gsequence in sequence_files:
                    self.manager.set_sequence(sequence_path = gsequence,
                                              sample_name = str(gsequence.parent))
                    
    def load_files(self):
        files = load_files(self)
        if files: 
            sequence_files = self.load_data(files)
            if sequence_files:
                for gsequence in sequence_files:
                    self.manager.set_sequence(sequence_path = gsequence,
                                              sample_name = str(gsequence.parent))
        

    def load_data(self, files:list[Path]):
        sequence_files = []
        for file in files:
            if 'GSequence' in file.suffix:
                    sequence_files.append(file)
                    continue
            try:
                experiment = self.loader.create_experiment(str(file))
                if experiment is not None:
                    sample = self.manager.add_experiment(experiment, sample_name=str(file.parent))
                self.refresh_sample_in_model(sample)
            except Exception as e:
                continue

        return sequence_files

    def refresh_sample_in_model(self, sample):
        parent_item = None
        for row in range(self.model.rowCount()):
            item = self.model.item(row)
            if item and item.data(Qt.UserRole) == sample:
                parent_item = item
                break
        
        if not parent_item:
            parent_item = QStandardItem(f"{sample.sample_name}")
            parent_item.setData(sample, Qt.UserRole)
            self.model.appendRow(parent_item)
        
        parent_item.setRowCount(0)
        for exp in sample.experiments:
            self.add_experiment_to_item(parent_item, exp)

    def add_experiment_to_item(self, parent_item, exp):
        child_name = QStandardItem(exp.file_name)
        child_class = QStandardItem(exp.__class__.__name__)
        child_id = QStandardItem(str(exp.id))
        child_name.setData(exp, Qt.UserRole)
        parent_item.appendRow([child_name, child_class, child_id])

    def toggle_expand(self):
        if not self.expanded_all:
            self.tree_view.expandAll()
            self.expanded_all = True
        else:
            self.tree_view.collapseAll()
            self.expanded_all = False

    def filter_tree(self, text):
        self.proxy_model.setFilterFixedString(text)
        if text:
            self.tree_view.expandAll()
        else:
            self.tree_view.collapseAll()

    def get_selected_experiments(self):
        """Zwraca listę unikalnych obiektów eksperymentów z obecnego zaznaczenia (wsparcie wsteczne)."""
        _, objects, _ = self._get_business_objects_from_selection()
        return objects