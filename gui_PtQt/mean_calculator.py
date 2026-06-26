from PyQt5.QtWidgets import QTableView, QHBoxLayout, QVBoxLayout, QGridLayout, QWidget, QSplitter, QLabel, QPushButton, QDialog, QMessageBox
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtCore import Qt

import pandas as pd
import numpy as np

from core.experiments import Experiment
from core import ExperimentManager, analysis_manager

from core.experiments.analysis import MeanAnalysis

class MeanCalculator(QDialog):
    def __init__(self, parent = None, experiments = None):
        super().__init__(parent)

        self.default_analysis_prefix = 'Mean Curve'
        # setting up main widgets
        self.table = QTableView()
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['Experiment', 'X', 'Y'])
        self.table.setModel(self.model)

        self.joined_x = None
        self.joined_y = None

        self.populate(experiments = experiments)
        self.build_ui()
        self.exec()

    def build_ui(self):
        # layouts
        main_layout = QHBoxLayout()
        tree_layout = QVBoxLayout()
        result_layout = QVBoxLayout()

        main_layout.addLayout(tree_layout)
        main_layout.addLayout(result_layout)
        self.setLayout(main_layout)

        # adding main widgets
        tree_layout.addWidget(self.table)
        
        check_button = QPushButton('Check state')
        check_button.clicked.connect(self.calculate_mean)
        tree_layout.addWidget(check_button)

    def populate(self, experiments:list[Experiment]):

        for experiment in experiments:
            name_item = QStandardItem(experiment.file_name)
            name_item.setData(experiment, Qt.UserRole)
            check_x = QStandardItem('')
            check_y = QStandardItem('')
            checks = [check_x, check_y]
        
            for check in checks:
                check.setCheckState(Qt.CheckState.Unchecked)
                check.setCheckable(True)
            
            self.model.appendRow([name_item, check_x, check_y])

    def get_checked(self, column_index):
        
        checked_items = []
        for row in range(self.model.rowCount()):
            checked = self.model.item(row, column_index)
            if checked and checked.checkState() == Qt.CheckState.Checked:
                checked_items.append(True)
            elif checked and checked.checkState() == Qt.CheckState.Unchecked:
                checked_items.append(False)

        return checked_items

    def get_columns(self):

        x = self.get_checked(1)
        y = self.get_checked(2)
        rows = zip(x, y, range(self.model.rowCount()))
        
        final_x = []
        final_y = []
        for select_x, select_y, row in rows:
            experiment: Experiment = self.model.item(row, 0).data(Qt.UserRole)
            x_column, y_column = experiment.get_xy_data(0)

            if select_x:
                final_x.append(x_column)
            if select_y:
                final_y.append(y_column)
        
        if final_x:
            joined_x_df = pd.concat(final_x, axis = 1)
        else:
            QMessageBox.information(self, 'Select X', 'Please select at least one X column.')
            return
        
        if final_y:
            joined_y_df = pd.concat(final_y, axis = 1)
        else:
            QMessageBox.information(self, 'Select Y', 'Please select at least one Y column.')
            return

        self.joined_x = joined_x_df
        self.column_name_x = self.joined_x.columns[0]
        self.joined_y = joined_y_df
        self.column_name_y = self.joined_y.columns[0]


        return (joined_x_df, joined_y_df)

    def calculate_mean(self):
        
        self.get_columns()
        if (self.joined_x is not None) and (self.joined_y is not None):
            mean_x = self.joined_x.mean(axis = 1)
            std_x = self.joined_x.std(axis = 1)
            mean_y = self.joined_y.mean(axis = 1)
            std_y = self.joined_y.std(axis = 1)
            final_df = pd.concat([mean_x,std_x, mean_y, std_y], axis =1)

            columns = ['Mean X', 'Std X', 'Mean Y', 'Std Y']
            first_column_names = [self.column_name_x, self.column_name_x, self.column_name_y, self.column_name_y]
            final = zip(columns, first_column_names)
            final_df.columns = pd.MultiIndex.from_tuples(final)
            
            name = analysis_manager.ask_for_analysis_name(self.default_analysis_prefix)
            if name:
                analysis = MeanAnalysis(name = name, experiments = None, data = final_df, selection = None)
                analysis_manager.add_analysis(analysis)

        


