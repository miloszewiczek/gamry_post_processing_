from .base import *

class OpenCircuit(Experiment):
    def __init__(self, file_path, date_time, id, tag, cycle):
        super().__init__(file_path, date_time, id, tag, cycle)


    def _add_computed_column(self, curve:pd.DataFrame) -> pd.DataFrame:
        curve['E vs RHE [V]'] = curve['Vf'] + reference_potential
        curve['T [s]'] = curve['T']
        return curve[['T [s]', 'E vs RHE [V]']] 
    
    def get_multiindex_labels(self, columns, curve_index, add_curve_index = True) -> tuple[list[list[str]], list[str]]:
        """
        Returns levels and names for multiindexing. Is different for each 
        type of experiment.
        Returns:
        - list of lists: values for each level of the Multiindex (e.g. [[path], [curve_name], [column1, column2, column2, ...]])
        - list of level names (e.g. ['Path, 'Curve', 'Metric])
        """

        level_values = [[f'{self.file_path}'], [f'{self.meta_data['TIMEOUT']}'], columns]
        level_names = ['Path', 'Duration [s]', 'Parameter']
        return level_values, level_names