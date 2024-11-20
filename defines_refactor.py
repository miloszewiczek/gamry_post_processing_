import gamry_parser
import pandas as pd
from tabulate import tabulate

DTA_parser = gamry_parser.GamryParser()

class Experiment():
    def __init__(self, file_path):

        self.file_path = file_path
        self.Ru = 0

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
    def __init__(self):
        self.experiments = []
    
    def add_experiment(self, experiment):
        self.experiments.append(experiment)
    
    def get_experiments_by_type(self, experiment_type) -> list:

        tmp = [exp for exp in self.experiments if isinstance(exp, experiment_type)]
        if len(tmp) == 0:

            print(f'No experiments with tag {experiment_type}!')
            
        return tmp
    
    def batch_Ru(self, Ru_value:float = 0):
        
        for experiment in self.experiments:
            experiment.set_Ru(Ru_value)
        
    def list_details(self):
        '''Function to list the details of every file currently in the manager to stdout'''
        x = []
        for experiment in self.experiments:
            details = {'File Path': experiment.file_path,
                       'Ru [Ohm]': experiment.Ru}
            x.append(details)
        print(tabulate(x, headers='keys'))


def create_experiment(file_path, manager):
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
    
