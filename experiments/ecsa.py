from .base import *
from .cyclic_voltammetry import Voltammetry


class ECSA(Voltammetry):
    def __init__(self, file_path, date_time, id, tag, cycle):
        super().__init__(file_path, date_time, id, tag, cycle)

    def calculate_difference_at_potential(self, potential) -> float:
        '''A method to calculate the difference of current at a specific potential. The potential must lie
        between the potential limits from the experiment. This function needs to be combined with linear_regression
        method to calculate the double-layer capacitance.
        
        Args:
        self (Voltammetry): meta_data such as potential limits and i-E data
        potential: the potential in V, used to calculate the current difference
        
        Returns:
        average_difference: an average of all measurements within an experiment'''

        current_diff_list  = []
        #CHECKS WHETHER THE POTENTIAL LIES WITHIN THE EXPERIMENTAL LIMITS
        if self.meta_data['VLIMIT1'] > self.meta_data['VLIMIT2']:
            if potential > self.meta_data['VLIMIT1'] or potential < self.meta_data['VLIMIT2']:
                print('Potential out of range')
                return
        
        for curve in self.data_list:

            distances = (curve['Vf'] - potential).abs()
            minimal_distance_index = distances.argsort()[:2]
            current_values = curve.iloc[minimal_distance_index]['Im']
            result = abs(current_values.iloc[0] - current_values.iloc[1])
            #print(f'Difference at {potential} calculated to be {result}')
            
            current_diff_list.append(result)

        return np.mean(current_diff_list)
    
    def calculate_CDL_integral(self):
        '''A method to calculate the double-layer capacitance using the integral method:
        C_DL = integral(idv)/(2 * scanrate * potential window)
        
        Args:
        self (Experiment): Header and numerical data, including scan limits and i-E data
        
        Returns:
        average_capacitance: average value of all curves in the experiment, in Farads
        '''

        capacitance_list = []

        for curve in self.data_list:

            potential_data = curve['Vf']
            current_data = curve['Im']
            max_potential = potential_data.idxmax()
            
            integral_scan_forward = np.trapz(abs(current_data.loc[:max_potential + 1]), potential_data.loc[:max_potential + 1])
            integral_scan_backward = np.trapz(abs(current_data.loc[max_potential+1:]), potential_data.loc[max_potential+1:])   
            integral_area = abs(integral_scan_forward - integral_scan_backward)   

            potential_window = abs(self.meta_data['VLIMIT1'] - self.meta_data['VLIMIT2'])
            capacitance_times_scanrate = integral_area/(potential_window)
            capacitance_list.append(capacitance_times_scanrate)

        return np.mean(capacitance_list)
    
    def process_data(self):

        self.diff = []
        for potential in settings.options['potential']:
            print(messages.processing_messages['line_method_potential'].format(potential = potential))
            self.diff.append(self.calculate_difference_at_potential(potential = potential)) 
        self.integral = self.calculate_CDL_integral()
        self.processed_data  = super().process_data()
        return self.processed_data
    
    def get_parameter_dict(self):

        results_dict = {'id': self.id, 'integral': self.integral, 'diff': (self.diff)}
        #return {'Difference(s)': self.diff, 'Integral': self.integral}
        return results_dict
        