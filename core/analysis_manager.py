from experiments.analysis import BaseAnalysis
from typing import List, Callable
import pandas as pd
import numpy as np
from gui_PtQt.pandas_viewer import AnalysisViewer

class AnalysisManager():
    """
    Aggregator and manager of analyses objects.
    """

    def __init__(self):

        self._analyses: List[BaseAnalysis] = []
        self._on_analysis_added_callbacks: List[Callable[[BaseAnalysis, None]]] = []
        self.current_analysis_number = 1

    def register_on_added(self, callback: Callable[[BaseAnalysis], None]):
        self._on_analysis_added_callbacks.append(callback)

    def add_analysis(self, analysis_obj: BaseAnalysis) -> None:
        """
        Append to analyses container.
        
        Args:
            analysis_obj (BaseAnalysis): Analysis to add.
            
        Returns:
            None
        """

        self._analyses.append(analysis_obj)
        self.current_analysis_number += 1

        for callback in self._on_analysis_added_callbacks:
            try:
                callback(analysis_obj)
            except Exception as e:
                print(f'Callback failed during callback {e}')
        
    def get_current_analysis_number(self):
        return self.current_analysis_number
    
    def get_all(self) -> List[BaseAnalysis]: 
        return self._analyses
    
    def delete_analysis(self, analysis_obj: BaseAnalysis) -> BaseAnalysis:
        """
        Delete analysis.

        Args:
            analysis_obj (BaseAnalysis): Analysis to delete.

        Returns:
            deleted_analysis (BaseAnalysis): Deleted analysis. 
        """

        deleted_analysis = self._analyses.pop(analysis_obj)
        return deleted_analysis
    
    def get_analysis_by_name(self, analysis_name:str) -> BaseAnalysis | None:
        """
        Get analysis by name.
        
        Args: 
            analysis_name (str): Name of the analysis to get.
            
        Returns:
            analysis (BaseAnalysis): Analyis of the correct name.
        """
        
        for analysis in self.analyses:
            if getattr(analysis, 'name') == analysis_name:
                return analysis
        else:
            return
        
    def save_iteratively(self):
        
        with pd.ExcelWriter('test.xlsx', 'openpyxl', mode = 'w') as writer:
            for analysis in self._analyses:
                data = analysis.get_data()
                for sheet_name, data_set in data.items():
                    data_set:pd.DataFrame
                    data_set.to_excel(writer, sheet_name = sheet_name)

        
    def __iter__(self):
        return iter(self.analyses)
    
    def __repr__(self):
        return f'AnalysisManager. Current analyses amount: {len(self.analyses)}'
    
analysis_manager = AnalysisManager()


from PyQt5.QtWidgets import QWidget, QTreeView, QPushButton, QLabel, QVBoxLayout
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, pyqtSignal, QObject

class AnalysisTreeModel(QStandardItemModel):
    def __init__(self, manager: AnalysisManager, parent = None):
        super().__init__(parent)
        
        self.manager = manager
        self.setHorizontalHeaderLabels(['Name', 'Value'])

        # Registering the callback
        self.manager.register_on_added(self._handle_analysis_added)

        for analysis in self.manager.get_all():
            self._add_analysis_to_tree(analysis)

    def _handle_analysis_added(self, analysis:BaseAnalysis):

        self._add_analysis_to_tree(analysis)

    def _add_analysis_to_tree(self, analysis:BaseAnalysis):
        
        root_item = QStandardItem(analysis.name)
        root_item.setData(analysis, Qt.ItemDataRole.UserRole)
        self.appendRow([root_item, QStandardItem("")])

        subitems = analysis.get_dictionary()
        for key, value in subitems.items():
            subitem_name = QStandardItem(key)
            subitem_name.setData(value, Qt.ItemDataRole.UserRole)

            try:
                subitem_value = QStandardItem(value)
            except:
                subitem_value = QStandardItem(value.__class__.__name__)
            subitem_value.setData(value, Qt.ItemDataRole.UserRole)

            root_item.appendRow([subitem_name, subitem_value])
    
        

class AnalysisWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.analysis_manager = analysis_manager
        self.tree_view = QTreeView()
        self.model = AnalysisTreeModel(self.analysis_manager)
        self.tree_view.setModel(self.model)
        self.tree_view.doubleClicked.connect(self._on_double_clicked)
        
        self.build_ui()

    def build_ui(self):

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tree_view)

        save_btn = QPushButton('Save!')
        save_btn.clicked.connect(self.analysis_manager.save_iteratively)

        main_layout.addWidget(save_btn)
        self.setLayout(main_layout)

    def _on_double_clicked(self, index):
        
        if index.column() != 0:
            index = index.siblingAtColumn(0)

        identity = index.data(Qt.UserRole)
        self.handle_object(identity)


    def handle_object(self, object):
        
        match object:
            
            case str():
                print(object)
            case int():
                print(object)
            case pd.DataFrame():
                x = AnalysisViewer(object)
