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
                pass
        
        for curve in self.data_list:

            distances = (curve['Vf'] - potential).abs()
            minimal_distance_index = distances.argsort()[:2]
            current_values = curve.iloc[minimal_distance_index]['Im']
            result = abs(current_values.iloc[0] - current_values.iloc[1])
            print(f'Difference at {potential} calculated to be {result}')
            
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
            capacitance = integral_area/(2 * potential_window * self.meta_data['SCANRATE'])
            print(capacitance)
            capacitance_list.append(capacitance)

        return np.mean(capacitance_list)
        

class Chronoamperometry(Experiment):
    def __init__(self, file_path):
        self.file_path = file_path
        pass

class EIS(Experiment):
    def __init__(self, file_path):
        self.file_path = file_path
        pass

class Data_Processor():
    def __init__(self):
        pass


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
            if 'TAG' in line:
                experiment_tag = line.split()[1]
                break

    '''
    tmp_experiment.load_data()
    tmp_TAG = tmp_experiment.TAG
    '''

    experiment_classes = {
        "CV" : Voltammetry,
        "CHRONOA" : Chronoamperometry,
        "EIS" : EIS
    }

    experiment_class = experiment_classes.get(experiment_tag)

    if not experiment_class:
        #print(f'Unknown type of experiment {experiment_tag}. Updating the list of experiments')
        experiment_classes[experiment_tag] = Experiment
        experiment_class = experiment_classes.get(experiment_tag)

    manager.add_experiment(experiment_class(file_path))
    return experiment_class(file_path)
    
