from .base import *

class Voltammetry(Experiment):
    def __init__(self, file_path, date_time, id, tag, cycle):
        super().__init__(file_path, date_time, id, tag, cycle)

    def print_potential_path(self):

        E_start = self.meta_data['VINIT']
        E1 = self.meta_data['VLIMIT1']
        E2 = self.meta_data['VLIMIT2']
        E_end = self.meta_data['VFINAL']
        cycles = self.meta_data['CYCLES']
        scan_rate = self.meta_data['SCANRATE']

        print('\nAll potential values in Volts!')
        print('E_START ----> (E1 <----> E2)x cycles ----> E_FINAL')
        print('Scan rate: ', scan_rate)
        print('==============================================')
        print(f'{E_start} ----> ({E1} <----> {E2})x{cycles} ----> {E_end}')
        print('==============================================\n')

    def process_data(self) -> pd.DataFrame:
        
        result = super().process_data()

        return result

    def _add_computed_column(self, curve):
        CV_curve =  super()._add_computed_column(curve)
        return CV_curve

    def get_multiindex_labels(self, columns, curve_index, add_curve_index=True):

        level_values = [[f'{self.file_path}'], [f'Curve {curve_index}'], columns]
        level_names = ['Path', 'Curve number', 'Parameter']
        return level_values, level_names
