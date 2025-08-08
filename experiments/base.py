import pandas as pd
import numpy as np
import gamry_parser
DTA_parser = gamry_parser.GamryParser()
from matplotlib import pyplot as plt
from collections import defaultdict
from utilities.other import ask_user
from app_config import messages, settings

reference_potential = settings.options['reference_potential']
geometrical_area = settings.options['geometrical_area']

class Experiment():
    def __init__(self, file_path, date_time, id, tag, cycle):

        self.file_path = file_path
        self.date_time = date_time
        self.id = id
        self.tag = tag
        self.parameters = {}
        self.processed_data = []
        self.cycle = cycle

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
        self.Ru = Ru_value
    
    def _add_computed_column(self, curve:pd.DataFrame) -> pd.DataFrame:

        curve['J_GEO [A/cm2]'] = curve['Im']/geometrical_area
        curve['E vs RHE [V]'] = curve['Vf'] + reference_potential

        if hasattr(self, 'Ru'):
            curve['E_iR vs RHE [V]'] = curve['Vf'] + reference_potential - self.Ru * curve['Im']
            return curve[['E vs RHE [V]', 'E_iR vs RHE [V]', 'J_GEO [A/cm2]']]
        
        curve = curve.reset_index(drop=True)

        return curve[['E vs RHE [V]', 'J_GEO [A/cm2]']]

    def process_data(self, **kwargs) -> pd.DataFrame:
        


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
            level_values, level_names = self.get_multiindex_labels(curve.columns, curve_index, add_curve_index= include_curve_index)
            curve.columns = pd.MultiIndex.from_product(level_values, names = level_names)
            dfs.append(curve)

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
    
    def get_curves(self, index:int|None):

        #None is a string, because the treeview stores values as strings!
        if index == "None":
            return self.data_list
        else:
            index = int(index)
            return [self.data_list[index]]