from .base import *

class EIS(Experiment):
    def __init__(self, file_path, date_time, id, tag, cycle):
        super().__init__(file_path, date_time, id, tag, cycle)
    
    def process_data(self):
        
        result = super().process_data()
        return result

    def get_multiindex_labels(self, columns, curve_index, add_curve_index = True) -> tuple[list[list[str]], list[str]]:
        """
        Returns levels and names for multiindexing. Is different for each 
        type of experiment.
        Returns:
        - list of lists: values for each level of the Multiindex (e.g. [[path], [curve_name], [column1, column2, column2, ...]])
        - list of level names (e.g. ['Path, 'Curve', 'Metric])
        """
        final_potential = self.meta_data['VDC'] + reference_potential
        final_potential = '{:.2f}'.format(final_potential)

        level_values = [[self.file_path], [final_potential], columns]
        level_names = ['Path', 'E vs RHE [V]', 'Parameter']
        return level_values, level_names


    def set_Ru(self, Ru_value):
        self.Ru = Ru_value
    
    def _add_computed_column(self, curve:pd.DataFrame) -> pd.DataFrame:
        
        curve = curve.reset_index(drop=True)
        curve = curve[['Freq','Zreal','Zimag']]
        curve.columns = ['Freq [Hz]', 'Zreal [Ohm]', 'Zimag [Ohm]']
        return curve