import gamry_parser
import pandas as pd
from tabulate import tabulate
import numpy as np

DTA_parser = gamry_parser.GamryParser()
geometrical_area = float(1.0)
reference_potential = float(0)


class Experiment():
    def __init__(self, file_path):

        self.file_path = file_path

    def load_data(self):
        
        DTA_parser.load(self.file_path)
        self.meta_data = DTA_parser.get_header()
        self.TAG = self.meta_data['TAG']
        self.data_list = DTA_parser.get_curves() 
        if len(self.data_list[-1].index) == 1:
            self.data_list.pop(-1)
            #print(f'Single point curve removed in file {self.file_path}')

    def join_curves(self) -> pd.DataFrame:
        
        return pd.concat(self.data_list)
    
    def set_Ru(self, Ru_value):
        self.Ru = Ru_value

    def process_data(self) -> pd.DataFrame:
        print(f'Processing data of {self.file_path}')
        print(f'Found {len(self.data_list)} curves')
        for  curve_index, data in enumerate(self.data_list):
            
            if isinstance(geometrical_area, float):
                self.data_list[curve_index]['J_GEO'] = data['Im']/geometrical_area
            if isinstance(reference_potential, float):
                self.data_list[curve_index]['E vs RHE'] = data['Vf'] + reference_potential
            if isinstance(self.Ru, float):
                self.data_list[curve_index]['E_iR vs RHE'] = data['Vf'] - self.Ru * data['Im']

class OpenCircuit(Experiment):
    def __init__(self, file_path):
        super().__init__(file_path)

class LinearVoltammetry(Experiment):
    def __init__(self, file_path):
        super().__init__(file_path)
        self.tafel_curves = []

    def process_data(self) -> pd.DataFrame:

        super().process_data()
        for curve in self.data_list:
            curve['log10 J_GEO'] = np.log10(0-curve['J_GEO'])
            tafel_curve = curve[['log10 J_GEO', 'E vs RHE']]
            self.tafel_curves.append(tafel_curve)

class Voltammetry(Experiment):
    def __init__(self, file_path):
        super().__init__(file_path)

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

class ECSA(Voltammetry):
    def __init__(self, file_path):
        super().__init__(file_path)
    

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
            capacitance = integral_area/(2 * potential_window * self.meta_data['SCANRATE']/1000)
            capacitance_list.append(capacitance)

        return np.mean(capacitance_list)

class Chronoamperometry(Experiment):
    def __init__(self, file_path):
        super().__init__(file_path)
    
    def process_data():
        pass

    def get_current_at_time(self, time):
        '''Method to get current at specific time. This functionality is mainly for 
        sampled voltammetry, where one wishes to eliminate the non-faradaic currents.
        
        Args:
        self (Chronoamperometry): i-E data, meta_data containing the applied potential
        time (Float or Int): the timestamp at which the current is read. Must be within the time limits
        
        Returns:
        current (float)'''

        for curve in self.data_list:
            
            closest_index = (curve['T'] - time).abs().idxmin()
            current = curve.iloc[closest_index]['Im']
            print(current)
        
        
class EIS(Experiment):
    def __init__(self, file_path):
        self.file_path = file_path
        pass

def calculate_ECSA_from_slope(ECSA_experiments: list, *args) -> list:
    '''Function to perform the calculate_difference_at_potential on
    provided ECSA experiments in different potentials and fit the 
    data to a linear regression model.
    The CDL is calculated as the slope of the function:
    
    di = CDL * v,
    where: di - difference in charging currents, v - scanrate
    
    
    Args:
    ECSA_experiments: list of ECSA objects,
    *args: an array of potential values to compute the current difference
    
    Returns:
    results: a list of linear slopes, representing the CDL.
    '''

    difference_list = []
    results = []

    for potential in args:

        for experiment in ECSA_experiments:
            experiment.load_data()
            difference = experiment.calculate_difference_at_potential(potential)
            scanrate = experiment.meta_data['SCANRATE'] / 1000
            difference_list.append((scanrate, difference))
        x = pd.DataFrame(difference_list)
        slope, intercept = np.polyfit(x.iloc[:,0], x.iloc[:,1], 1)
        results.append(slope)

    return results

def batch_integral_ECSA(ECSA_experiments: list) -> pd.DataFrame:
    '''Automation function to perform the calculate_CDL_integral on
    provided ECSA experiments.
    
    Args:
    ECSA_experiments: list of ECSA objects'''

    results = []

    for experiment in ECSA_experiments:
        try:
            x = experiment.calculate_CDL_integral()
        except:
            experiment.load_data()
            x = experiment.calculate_CDL_integral()
        results.append(x)

    return results

def batch_processing(list_of_experiments: list):

    for experiment in list_of_experiments:
        experiment.process_data()
    
def ECSA_difference(ECSA_experiments: list, *args):
    '''A function to compare the ECSA values obtained via the line and integral method.
    Work in progress to find the way to compare multiple potentials. As of now, only one
    potential is accepted. Additionally, functionality with EIS needs to be implemented.
    
    Args:
    ECSA_experiments: the list of ECSA objects to perform the analysis,
    *args: the potentials at which to calculate the CDL using the line method
    
    Returns:
    result: the smallest difference between the CDL values obtained via the two methods'''

    CDL_integrals = batch_integral_ECSA(ECSA_experiments)
    CDL_linear_slopes = calculate_ECSA_from_slope(ECSA_experiments, *args)

    result = min(abs(CDL_integrals - CDL_linear_slopes[0]))
    print(result)

class ExperimentManager():
    '''An interface class to aggregate and manage the experiments. '''

    def __init__(self):
        '''All of the experiments are stored in the variable self.experiments'''
        self.experiments = []
    
    def add_experiment(self, experiment):
        self.experiments.append(experiment)

    def delete_experiment(self, experiment):
        self.experiments.remove(experiment)
    
    def get_experiments_by_type(self, experiment_type) -> list:

        tmp = [exp for exp in self.experiments if isinstance(exp, experiment_type)]
        if len(tmp) == 0:

            print(f'No experiments with tag {experiment_type}!')
            
        return tmp
    
    def batch_Ru(self, Ru_value:float = 0):
        '''A method to apply the Ru parameter to all experiments'''
        
        for experiment in self.experiments:
            experiment.set_Ru(Ru_value)
        
    def list_details(self):
        '''Function to list the details of every file currently in the manager to stdout'''
        x = []
        for experiment in self.experiments:
            details = experiment.__dict__
            x.append(details)
        print(tabulate(x, headers='keys'))


def create_experiment(file_path, manager):
    '''Factory function to create the experiment and store it in a manager.
    Depending on the TAG of the .DTA file, it creates a different experiment object characterized by different data processing methods.'''
    with open(file_path, 'r') as tmp_experiment:
        lines = tmp_experiment.readlines()

        if len(lines) == 0:
            return

        for line in lines:
            if 'TITLE' in line:
                experiment_tag = line.split()[2]
                break

    '''
    tmp_experiment.load_data()
    tmp_TAG = tmp_experiment.TAG
    '''

    experiment_classes = {
        #"CV" : Voltammetry,
        #"CHRONOA" : Chronoamperometry,
        #"EIS" : EIS,
        "HER" : LinearVoltammetry,
        "OCP" : OpenCircuit,
        "ECSA" : ECSA
    }

    experiment_class = experiment_classes.get(experiment_tag)

    if not experiment_class:
        #print(f'Unknown type of experiment {experiment_tag}. Updating the list of experiments')
        experiment_classes[experiment_tag] = Experiment
        experiment_class = experiment_classes.get(experiment_tag)

    manager.add_experiment(experiment_class(file_path))
    return experiment_class(file_path)
    
