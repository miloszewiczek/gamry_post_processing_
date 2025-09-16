import pandas as pd
import numpy as np
import gamry_parser
from matplotlib import pyplot as plt
from collections import defaultdict
from app_config import messages, settings
from typing import Literal
from unicode_mapping import uni_map
import os

DTA_parser = gamry_parser.GamryParser()

class Experiment():
    def __init__(self, file_path, date_time, id, tag, cycle):

        self.file_path = file_path
        self.folder = os.path.dirname(file_path)
        self.file_name = os.path.basename(file_path)
        self.date_time = date_time
        self.id = id
        self.tag = tag
        self.parameters = {}
        self.processed_data = []
        self.cycle = cycle
        self.default_x = 'E vs RHE [V]'
        self.default_y = 'J_GEO [A/cm2]'
        self.geometrical_area = 1
        self.reference_potential = 0
        self.Ru = 0

    def load_data(self):
        
        DTA_parser.load(self.file_path)
        self.meta_data = DTA_parser.get_header()
        self.TAG = self.meta_data['TAG']
        self.data_list = DTA_parser.get_curves() 
        if len(self.data_list[-1].index) == 1:
            self.data_list.pop(-1)
            #print(f'Single point curve removed in file {self.file_path}')
        return self.meta_data


    def get_multiindex_labels(self, columns, curve_index, add_curve_index = True) -> tuple[list[list[str]], list[str]]:
        """
        Returns levels and names for multiindexing. Is different for each 
        type of experiment.
        Returns:
        - list of lists: values for each level of the Multiindex (e.g. [[path], [curve_name], [column1, column2, column2, ...]])
        - list of level names (e.g. ['Path, 'Curve', 'Metric])
        """

        level_values = [[self.file_path], [curve_index], columns]
        level_names = ['Path', 'Curve', 'Parameter']
        return level_values, level_names


    def set_Ru(self, Ru_value):
        print(self.__class__.__name__, 'set Ru of ', str(Ru_value))
        self.Ru = Ru_value
    
    def _add_computed_column(self, curve:pd.DataFrame) -> pd.DataFrame:

        curve['J_GEO [A/cm2]'] = curve['Im']/self.geometrical_area
        curve['E vs RHE [V]'] = curve['Vf'] + self.reference_potential
        curve = curve.reset_index(drop=True)

        if self.Ru != 0:
            self.default_x = 'E_iR vs RHE [V]'
            curve['E_iR vs RHE [V]'] = curve['Vf'] + self.reference_potential - self.Ru * curve['Im']
            return curve[['E vs RHE [V]', 'E_iR vs RHE [V]', 'J_GEO [A/cm2]']]

        return curve[['E vs RHE [V]', 'J_GEO [A/cm2]']]

    def process_data(self, **kwargs) -> list[pd.DataFrame]:
        
        print(messages.processing_messages['processing_data_fp_id_len'].format(
            file_path = self.file_path,
            id = self.id,
            number_of_curves = len(self.data_list)
            ))
        
        dfs = []
        for  curve_index, curve in enumerate(self.data_list):
            
            processed_curve = self._add_computed_column(curve)

            dfs.append(processed_curve)
        
        self.processed_data = dfs

        return self.processed_data
    
    def make_multiindex(self, data):

        dfs = []
        
        if len(data) > 1:
            include_curve_index = True
        else:
            include_curve_index = False

        for curve_index, curve in enumerate(data):
            curve_copy = curve.copy()
            level_values, level_names = self.get_multiindex_labels(curve_copy.columns, curve_index, add_curve_index= include_curve_index)
            curve_copy.columns = pd.MultiIndex.from_product(level_values, names = level_names)
            dfs.append(curve_copy)

        return pd.concat(dfs, axis=1)

    def get_tree_structure(self) -> dict:
        """Return a nested dictionary representing the file → [curve or potential] → parameters tree.
    Supports both 2- and 3-level MultiIndex DataFrames."""
    
        if not hasattr(self, "processed_data"):
            raise ValueError("Run process_data() first.")

        df = self.processed_data
        tree = defaultdict(lambda: defaultdict(list))

        if isinstance(df.columns, pd.MultiIndex):
            for col_tuple in df.columns:
                if len(col_tuple) == 3:
                    path, middle, param = col_tuple
                    tree[path][middle].append(param)
                elif len(col_tuple) == 2:
                    path, param = col_tuple
                    tree[path]["[no group]"].append(param)  # placeholder label
                else:
                    raise ValueError(f"Unsupported column depth: {len(col_tuple)}")
        else:
            # fallback: single-level column (not MultiIndex)
            tree[self.file_path]["[flat]"] = list(df.columns)

        return dict(tree)
    
    def perform_postprocessing(self):
        return 'Base class has no postprocessing defined'

    def get_data(self, index:int|None, data_type: str = Literal['data_list', 'processed_data']):
        #Need to add functionality to get either self.data_list or processed_list or even something different
        #None is a string, because the treeview stores values as strings!

        data = getattr(self, data_type)
        
        if index == "None" or index == None:
            return data 
        else:
            index = int(index)
            return [data[index]]
        
    def get_columns(self, axis: Literal['x','y','both'], columns:list = None):
        '''Helper function that returns the default column name stored in default_x or default_y'''

        match axis:
            case 'x':
                return self.default_x
            case 'y':
                return self.default_y
            case 'both':
                return self.default_x, self.default_y
        
        if columns is not None:
            try:
                return self.processed_data[0][columns]
            except:
                print(f'No column {columns}')

    def get_meta_data(self) -> dict:
        return self.meta_data

    def get_essentials(self):

        essentials = {
            'Filepath': (self.file_path, 'LABEL', str, 'file_path'),
            'Experiment ID': (self.id, 'LABEL', int, 'id'),
            'Experiment TAG': (self.meta_data['TAG'], 'LABEL', str, 'TAG'),
            'Number of curves': (len(self.data_list), 'LABEL', int, 'NONE'),
            'Title': (self.meta_data['TITLE'],'LABEL', str, 'TITLE'),
            'Potentiostat': (self.meta_data['PSTAT'],'LABEL', str, 'PSTAT'),
            'Date | Time': (" | ".join([self.meta_data['DATE'], self.meta_data['TIME']]), 'LABEL', str, 'NONE'),
            f'Area [cm{uni_map['square']}]': (self.geometrical_area, 'ENTRY', float, 'geometrical_area'),
            'Reference Potential [V]': (self.reference_potential, 'ENTRY', float, 'reference_potential'),
            f'Ru [{uni_map['Ohm']}]': (self.Ru, 'ENTRY', float, 'Ru')
        }
        return essentials
    