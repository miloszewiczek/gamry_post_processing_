import gamry_parser
import pandas as pd
from tabulate import tabulate
import numpy as np
from itertools import chain
from datetime import datetime
import re
from collections import defaultdict
import os
from functools import wraps
import matplotlib.pyplot as plt
from config import config, messages
from openpyxl import Workbook, load_workbook

DTA_parser = gamry_parser.GamryParser()


def create_empty_excel(file_name: str):
    if not os.path.exists(file_name):
        wb = Workbook()
        ws = wb.active
        ws.title = "temp"  # dummy sheet
        wb.save(file_name+'.xlsx')

def ask_user(prompt_string, input_types, *format_args, **format_kwargs):
    while True:
        user_input = input(prompt_string.format(*format_args, **format_kwargs))
        
        if not isinstance(input_types, (tuple, list)):  # If one type was provided, change it into tuple
            input_types = (input_types,)

        for input_type in input_types:
            try:
                return input_type(user_input)  # Try to cast the type 
            except ValueError:
                continue  #if ValueError, goes to another type

        print(f"Wrong input type. Expected one of: {', '.join(t.__name__ for t in input_types)}. Try again.")

def add_metadata(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        dataframe_list = func(self, *args, **kwargs)

        if not isinstance(dataframe_list, list):
            raise TypeError("Process_data needs to return a list object!")
        
        for number ,dataframe in enumerate(dataframe_list):

            file_row = pd.DataFrame([[self.file_path] * len(dataframe.columns)], columns = dataframe.columns)
            unit_row = pd.DataFrame([[config['units_mapping'].get(col, " ") for col in dataframe.columns]], columns = dataframe.columns)
    
            tmp = pd.concat([file_row, unit_row, dataframe], ignore_index = False)
            dataframe_list[number] = tmp
    return wrapper


class Experiment():
    def __init__(self, file_path, date_time, id, tag, cycle):

        self.file_path = file_path
        self.date_time = date_time
        self.id = id
        self.tag = tag
        self.parameters = {}
        self.processed_data_list = {}
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

    def join_curves(self, option='last') -> pd.DataFrame:

        match option:
            case 'last':
                self.data_list = self.data_list[-1]
            case 'first':
                self.data_list = self.data_list[0]
            case 'all':
                self.data_list = [df.reset_index(drop=True) for df in self.data_list]
                self.data_list = pd.concat(self.data_list, axis=1)
            case int() as idx if 0 <= idx < len(self.data_list):
                self.data_list = self.data_list[idx]
            case list() as idx_list:
                if all(isinstance(i, int) and 0 <= i < len(self.data_list) for i in idx_list):
                    self.data_list = pd.concat([self.data_list[i].reset_index(drop=True) for i in idx_list], axis=1)
            
        return self.data_list

    
    def get_additional_dataframes(self) -> dict[str, pd.DataFrame]:
        return {}

    def set_Ru(self, Ru_value):
        self.Ru = Ru_value
    
    def process_data(self, columns_to_keep = ['E vs RHE', 'J_GEO'], **kwargs) -> list[pd.DataFrame]:
        print(f'Processing data of {self.file_path} with id: {self.id} ({len(self.data_list)} curves).')
        for  curve_index, curve in enumerate(self.data_list):
            
            geometrical_area = config['default_settings']['geometrical_area']
            reference_potential = config['default_settings']['reference_potential']

            if isinstance(geometrical_area, float):
                curve['J_GEO'] = curve['Im']/geometrical_area
            if isinstance(reference_potential, float):
                curve['E vs RHE'] = curve['Vf'] + reference_potential
            if hasattr(self, 'Ru'):
                curve['E_iR vs RHE'] = curve['Vf'] - self.Ru * curve['Im']
                columns = columns_to_keep.append('E_iR vs RHE')
                curve = self.data_list[curve_index][columns]
                
            else:
                columns = columns_to_keep
                curve = self.data_list[curve_index][columns]
            self.data_list[curve_index] = curve
            
        return self.data_list


    
class OpenCircuit(Experiment):
    def __init__(self, file_path, date_time, id, tag, cycle):
        super().__init__(file_path, date_time, id, tag, cycle)


class LinearVoltammetry(Experiment):
    def __init__(self, file_path, date_time, id, tag, cycle):
        super().__init__(file_path, date_time, id, tag, cycle)
        self.tafel_curves = []
    
    def process_data(self) -> pd.DataFrame:
        
        try:
            GEO = config['default_settings']['GEO']
        except:
            GEO = -10

        super().process_data(columns_to_keep=['E vs RHE',  'J_GEO'])
        for curve_index, curve in enumerate(self.data_list):
            curve['log10 J_GEO'] = np.log10(0-curve['J_GEO'])
            
            tafel_curve = curve[['log10 J_GEO', 'E vs RHE']]
            self.tafel_curves.append(tafel_curve)
            try:
                curve = curve[['E_iR vs RHE', 'E vs RHE', 'J_GEO']]
            except:
                curve = curve[['E vs RHE', 'J_GEO']]
            self.data_list[curve_index] = curve
            self.calculate_overpotentials(curve, GEO = GEO)

        return self.data_list

    def calculate_overpotentials(self, curve:pd.DataFrame, ECSA = None, GEO = -10):

        tmp = {}
        if not isinstance(GEO, list):
            GEO = [GEO]

        for current in GEO:
            if current < 0: 
                mask = curve['J_GEO'] * 1000 < current
            elif current > 0:
                mask = curve['J_GEO'] * 1000  > current
            
            index = mask.idxmax()
            tmp[current] = ( curve.at[index, 'E vs RHE'] )
            
            self.overpotential = tmp
        return tmp

    def get_parameter_dict(self):
        return self.overpotential
    
    def get_additional_dataframes(self) -> dict[str, pd.DataFrame]:
        
        if self.tafel_curves:
            return {'tafel': pd.concat([df.reset_index(drop=True) for df in self.tafel_curves], axis=1)}
        return {}

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
        for potential in config['default_settings']['line_potential']:
            print('Calculating difference at potential: ', potential)
            self.diff.append(self.calculate_difference_at_potential(potential = potential)) 
        self.integral = self.calculate_CDL_integral()
        super().process_data()
        return self.data_list
    
    def get_parameter_dict(self):

        results_dict = {'id': self.id, 'integral': self.integral, 'diff': (self.diff)}
        #return {'Difference(s)': self.diff, 'Integral': self.integral}
        return results_dict
        

class Chronoamperometry(Experiment):
    def __init__(self, file_path, date_time, id, tag, cycle):
        super().__init__(file_path, date_time, id, tag, cycle)
        self.current = None
    
    def process_data(self):

        super().process_data(columns_to_keep=['T', 'J_GEO'])
        self.get_current_at_time(config['default_settings']['time_chrono'])
        return self.data_list


    def get_current_at_time(self, time):
        '''Method to get current at specific time. This functionality is mainly for 
        sampled voltammetry, where one wishes to eliminate the non-faradaic currents.
        
        Args:
        self (Chronoamperometry): i-E data, meta_data containing the applied potential
        time (Float or Int): the timestamp at which the current is read. Must be within the time limits
        
        Returns:
        current (float)
        '''

        for curve in self.data_list:
            maximum_time = curve['T'].iloc[-1]
            if time > maximum_time:
                time_input = ask_user(messages['input_messages']['time_not_in_range'], (float, int), time_in_seconds = maximum_time)
                return self.get_current_at_time(time_input)

            closest_index = (curve['T'] - time).abs().idxmin()
            current = curve.iloc[closest_index]['J_GEO']
            self.current = current
            return current
        
    def get_parameter_dict(self):

        results_dict = {'id': self.id, 'current': self.current}
        return results_dict
    


class EIS(Experiment):
    def __init__(self, file_path, date_time, id, tag, cycle):
        super().__init__(file_path, date_time, id, tag, cycle)
 
def calculate_ECSA_from_slope(ECSA_experiments: list[ECSA], potential_list:list, *args) -> list:
    """Function to perform the calculate_difference_at_potential on
    provided ECSA experiments in different potentials and fit the 
    data to a linear regression model.
    The CDL is calculated as the slope of the function:
    
    di = CDL * v,
    where: di - difference in charging currents, v - scanrate
    
    - `ECSA_experiments`: list of ECSA objects,
    - `potential_list`: an array of potential values to compute the current difference

    Returns:
    - `results`: a list of linear slopes, representing the CDL.
    """

    if isinstance(potential_list, float) or isinstance(potential_list, int):
        potential_list = [potential_list]

    difference_list = []
    results = []

    for potential in potential_list:

        for experiment in ECSA_experiments:
            if not hasattr(experiment,'data_list'):
                experiment.load_data()
            difference = experiment.calculate_difference_at_potential(potential)
            integral = experiment.calculate_CDL_integral()
            scanrate = experiment.meta_data['SCANRATE'] / 1000
            difference_list.append((scanrate, difference, integral))
        x = pd.DataFrame(difference_list)
        
        slope1, intercept = np.polyfit(x.iloc[:,0], x.iloc[:,1], 1)
        slope2, intercept2 = np.polyfit(x.iloc[:,0], x.iloc[:,2],1)
        #x['slope_line'] = slope1
        #x['slope_integral'] = slope2
        #x.to_excel(f'{input('Give excel name: ')}.xlsx')
        results.append(x)

    return (slope1, slope2), x

def batch_integrate_ECSA(ECSA_experiments: list) -> pd.DataFrame:
    '''Automation function to perform the calculate_CDL_integral on
    provided ECSA experiments.
    
    Args:
    ECSA_experiments: list of ECSA objects'''

    results = []

    for experiment in ECSA_experiments:
        print(experiment)
        try:
            x = experiment.calculate_CDL_integral()
        except:
            experiment.load_data()
            x = experiment.calculate_CDL_integral()
        results.append(x)

    return results

    
def calculate_ECSA_difference(ECSA_experiments: dict, potential_list:list , calc_eis: bool = False, DifferenceTable = True, *args):
    """A function to compare the ECSA values obtained via the line and integral method.
    Work in progress to find the way to compare multiple potentials. As of now, only one
    potential is accepted. Additionally, functionality with EIS needs to be implemented.
    
    Args:
    ECSA_experiments: the list of ECSA objects to perform the analysis,
    *args: the potentials at which to calculate the CDL using the line method
    
    Returns:
    result: the smallest difference between the CDL values obtained via the two methods
    """
    df_tmp = []
    full_data = []
    if calc_eis == True:
        EIS_CDL = float(input('Jaki CDL z dopasowania?\n'))
    for experiment_keys, experiments in ECSA_experiments.items():
        
        if potential_list == 'STEPSIZE':
            meta_data = experiments[0].load_data()
            step = meta_data['STEPSIZE']/1000
            limit1 = meta_data['VLIMIT1']
            limit2 = meta_data['VLIMIT2']
            potential_array = np.arange(min(limit1,limit2), max(limit1,limit2),step=step)
            CDL_linear_slopes = calculate_ECSA_from_slope(experiments, potential_list = potential_array, *args)
        elif isinstance(potential_list, int):
            potential = potential_list
            CDL_linear_slopes = calculate_ECSA_from_slope(experiments, potential_list = potential, *args)
        else:
            CDL_linear_slopes = calculate_ECSA_from_slope(experiments, potential_list = potential_list, *args)

        CDL_integrals = batch_integrate_ECSA(experiments)
    
        if DifferenceTable == True:
            table = []
            for integral in CDL_integrals:
                row = []
                for linear_slope in CDL_linear_slopes:
                    
                    if calc_eis == True:
                        result = abs(integral - EIS_CDL)
                    else:
                        result = abs(integral - linear_slope)
                    row.append(result)
                table.append(row)
            
            roznice = np.abs(np.array(CDL_integrals) - EIS_CDL)
            indeks_min = np.argmin(roznice)
            integral_closest = indeks_min

            roznice = np.abs(np.array(CDL_linear_slopes) - EIS_CDL)
            indeks_min = np.argmin(roznice)
            slopes_closest = indeks_min
            tmp = pd.DataFrame(table)
        
            return tmp, integral_closest, slopes_closest
        else:
            columns = ['integral slope'] + [potential_list]
            #columns = [str(scanrt) for scanrt in range(10,110,10)] + [potential_list]
            row = CDL_linear_slopes[0]
            full_data.append(CDL_linear_slopes[1])
            df = pd.DataFrame([row], columns = columns)
            df_tmp.append(df)
    df_tmp = pd.concat(df_tmp)
    full_data = pd.concat(full_data, axis=1)
    
    return df_tmp, full_data
        

class ExperimentManager():
    '''An interface class to aggregate and manage the experiments. '''

    def __init__(self):
        '''All of the experiments are stored in the variable self.experiments'''
        self.experiments = {}
        self.filtered = {}
        self.experiments_v2 = defaultdict(list)
        
        #Default settings, always implemented in the program
        self.experiment_classes = {
            'IDENTIFIERS':{
                "MYCIE" : Voltammetry,
                #"CHRONOA" : Chronoamperometry,
                #"EIS" : EIS,
                "HER" : LinearVoltammetry,
                "ECSA" : ECSA
                },
            'TAGS':{
                "CV" : Voltammetry,
                "LSV" : LinearVoltammetry,
                "OCP" : OpenCircuit,
                "CHRONOA" : Chronoamperometry,
                "EISPOT": EIS
                }
        
        }
        
        self.selected_experiments = None
        self.id_counter = 0


    def filter_by(self, name_startswith=None, cycle = None):
        pass
            
    def create_experiment(self, file_path):
        '''Factory function to create the experiment and store it in a manager.
        Depending on the TAG of the .DTA file, it creates a different experiment object characterized by different data processing methods.'''
        with open(file_path, 'r') as tmp_experiment:
            lines = tmp_experiment.readlines()

            if len(lines) == 0:
                return

            for line in lines:
                if 'TAG' in line:
                    experiment_tag = line.split()[1]
                if 'TITLE' in line:
                    match = re.search(r'LABEL\s+(.*?)\s+Test Identifier', line)
                    experiment_identifier = match.group(1)
                if 'DATE' in line:
                    experiment_date = line.split()[2]
                if 'TIME' in line:
                    experiment_time = line.split()[2]
                    try:
                        date_time = datetime.strptime(experiment_date + ' ' + experiment_time, '%d.%m.%Y  %H:%M:%S')
                    except ValueError:
                        date_time = datetime.strptime(experiment_date + ' ' + experiment_time, '%m/%d/%Y  %H:%M:%S')
                    break

        experiment_id = self.id_counter
        experiment_class = self.get_experiment_class(experiment_identifier = experiment_identifier,
                                                     experiment_tag = experiment_tag)
        
        experiment_keys = self.parse_filename(file_path, experiment_class)
        self.add_experiment(experiment_keys, experiment_class(
                                            file_path, 
                                            date_time, 
                                            experiment_id, 
                                            experiment_identifier,
                                            experiment_keys[1])) #CYCLE, NEED TO ADD IT TO ALL

        
        self.id_counter +=1
                    
    def get_experiment_class(self, experiment_identifier, experiment_tag):
        """Helper function to retrieve and in other case 
        add a new Experiment subclass to class fac"""

        #retrieve 
        experiment_class = self.experiment_classes['IDENTIFIERS'].get(experiment_identifier)

        if not experiment_class:
            experiment_class = self.experiment_classes['TAGS'].get(experiment_tag)
            if not experiment_class:
                self.experiment_classes['IDENTIFIERS'][experiment_identifier] = Experiment
                experiment_class = self.experiment_classes['IDENTIFIERS'].get(experiment_identifier)

        return experiment_class
    
    def parse_filename(self, filename:str, object_type:Experiment) -> tuple[str, int, Experiment]:
        """Helper function to parse the file given by filename and 
        returns a tuple containing experiment_name, cycle and type of the object"""
        match = re.match(r"(.+?)_#(\d+)(?:_#\d+)?\.DTA$", filename)
        if match:
            experiment_name = match.group(1)
            experiment_name = os.path.basename(experiment_name)
            cycle = int(match.group(2)) if match.group(2) else None


            return (experiment_name, cycle, object_type)
        match = re.match(r"(.+?).DTA$", filename)
        if match:

            experiment_name = match.group(1)
            experiment_name = os.path.basename(experiment_name)
            return (experiment_name, None, object_type)
        
    def add_experiment(self, experiment_keys, experiment):
        """
        Simple function to add an experiment based on a key obtained from parse_filename function
        - `experiment_keys`: a tuple of name, cycle and object type
        - `experiment`: the object of class Experiment or its subclass
        """
        self.experiments_v2[experiment_keys].append(experiment)

    def delete_experiment(self, id:list[int] = None, name:str = None):
        """
        Function to delete a list of experiments given either by their id (ints)
        or name via string. Should many files with similar name be found, the user will
        be promted to be more precise by using the check_name function.
        - `id`: list of integers to be deleted. Taken as None to check if the other condition is true
        - `name`: a name of experiment provided as a string
        """

        if isinstance(name, str):
            experiments = self.filter_experiments(name = name).values()
            id_to_delete1 = [self.check_name(experiments, name = name)]
        else:
            id_to_delete1 = []
            
        match id:
            case int():
                id_to_delete2 = [id]
            case list():
                id_to_delete2 = id
            case str():
                txt = id.split("-")
                lower_range = int(txt[0])
                higher_range = int(txt[1])
                print(txt)
                id_to_delete2 = list(range(lower_range, higher_range + 1))

        id_to_delete = id_to_delete1 + id_to_delete2
        print(id_to_delete)


        for _, experiment_list in self.experiments_v2.items():
            #NEEDS A COPY OF THE experiment_list (by using slicing) to avoid popping the original 
            #experimental list. This resulted in skipping items during iterations
            
            for experiment in experiment_list[:]:
                if experiment.id in id_to_delete:
                    print(f'Deleting file: {experiment.file_path} with id: {experiment.id}')
                    experiment_list.pop(experiment_list.index(experiment))
                    del experiment


    def check_name(self, experiment_list, name) -> int:
        """
        A helper function to check if an experiment with filepath corresponding to name argument
        exists within a list of experiments. 
        - `expriment_list`: mutable collection, most of the time a list
        - `name`: string to check if it exists within a list of Experiment objects

        - returns: id:int
        """

        tmp = chain(*experiment_list )
        tmp = [experiment for experiment in tmp if name in experiment.file_path]
        if len(tmp) == 0:
            print('No file found. Please try again.')
            return 
        
        elif len(tmp) == 1:
            return tmp[0].id
        elif len(tmp) > 1:
            self.list_items(experiment_collectible = tmp)
            print('Multiple files found. Please select an id or use full name to delete the file')
            inpt = input()
            try:
                inpt = int(inpt)
                return inpt
            except:
                return self.check_name(experiment_list, name = inpt)
            
    def combine_experiment(self, experiment_list):

        #NEED TO CHANGE THE DFS SO THAT CYCLE DON'T GET MIXED UP
        dfs = []
        for (name, cycle, object_type), experiments in experiment_list.items():

            print(experiments)

            for experiment in experiments:
                for i, df in enumerate(experiment.data_list):
                    df = df.reset_index(drop=True)
                    df.columns = pd.MultiIndex.from_product([
                        [f'exp{experiment.file_path}'], [f'curve {i}'], df.columns],
                        names = ['Path', 'Curve', 'Metric'])
                    dfs.append(df)
        return pd.concat(dfs, axis=1)

    
    def save_experiment(self, experiment_list:dict[Experiment] = None, file_name = 'test', option = 'last'):

        if experiment_list is None:
            experiment_list = self.experiments_v2

        if not os.path.exists(file_name):
            create_empty_excel(file_name)

        with pd.ExcelWriter(f'{file_name}.xlsx', mode='a', engine='openpyxl') as writer:
            for (name, cycle, object_type), experiments in experiment_list.items():
                print(messages['processing_messages']['processing_data'].format(experiment_type=name, cycle=cycle))

                # Join and collect primary data
                joined_data = []
                for experiment in experiments:
                    if not hasattr(experiment, 'data_list'):
                        continue  # or raise ValueError if it's critical
                    joined = experiment.join_curves(option=option)
                    joined_data.append(joined)

                # Save primary data
                primary_df = pd.concat(joined_data, axis=1)
                sheet_name = f'{name}_{cycle}'
                primary_df.to_excel(writer, sheet_name=sheet_name)

                # Save any additional data
                for experiment in experiments:
                    extra_data = experiment.get_additional_dataframes()
                    for suffix, df in extra_data.items():
                        extra_sheet_name = f"{name}_{cycle}_{suffix}"
                        df.to_excel(writer, sheet_name=extra_sheet_name)

                print(messages['processing_messages']['processing_done'].format(experiment_type=name, cycle=cycle))

        print(f'Data saved to {file_name}.xlsx')
        wb = load_workbook(file_name)
        if 'temp' in wb.sheetnames:
            std = wb['temp']
            wb.remove(std)
            wb.save(file_name)
    

    def filter_experiments(self, name=None, cycle=None, object_type=None):
        """
        Filter experiments by name, cycle or object type
        - `name`: str or list str (np. ["ECSA_#1", "CHRONO_#2_#1.DTA"])
        - `cycle`: str or list str (np. [1, 2])
        - `object`: str or list str (np. [CHRONOPOTENTOMETRY, ECSA])
        - `id`: WIP
        """
        print(f'Filtering experiments by:\nname: {name}\ncycle: {cycle}\nexperiment type: {object_type}')
        filtered_experiments = {
            key: files for key, files in self.experiments_v2.items()
            if (name is None or (isinstance(name, str) and name in key[0]) or (isinstance(name, list) and any(n in key[0] for n in name)))
            and (cycle is None or (isinstance(cycle, int) and key[1] == cycle) or (isinstance(cycle, list) and key[1] in cycle))
            and (object_type is None or (key[2] == object_type) or (isinstance(object_type, list) and key[2] in object_type))
        }
        self.filtered = filtered_experiments
        self.last_filter = {'name': name, 'cycle': cycle, 'object type': object_type}
        return self.filtered
    
    def get_experiments_by_id(self, id):
        
        if not isinstance(id, list):
            id = [id]

        tmp = []
        tmp2 = {key:None for key in id}

        for experiment in chain(*self.experiments_v2.values()):
            if experiment.id in id:
                tmp.append(experiment)
                tmp2[experiment.id] = experiment

        for id_number, experiment in tmp2.items():
            if experiment is not None:
                print(f'Retrieved experiment with id: {id_number}')
            else: 
                print(f'Failed to retrieve experiment with id: {id_number}')

        if len(tmp) == 1:
            return tmp[0]
        elif len(tmp) == 0:
            print(f'No experiments found')
        else:
            return tmp

    def list_items(self, experiment_collectible = None):
        """Function to print all experiments in the form of a table 
        from a collectible of experiments
        - `experiment_collectible: list or dict of Experiment objects
        """
        if experiment_collectible == None:
            experiment_collectible = self.experiments_v2

        if isinstance(experiment_collectible, dict):
            experiment_collectible = chain(*experiment_collectible.values())

        x = []
        head = ['id', 'file name', 'tag', 'object type', 'No of Curves']
        tmp_tag = None
        for d in experiment_collectible:
            if d.tag != tmp_tag:
                x.append([d.id, d.file_path, d.tag, type(d).__name__])
                tmp_tag = d.tag
                if hasattr(d, 'data_list'):
                    x[-1].append(len(d.data_list))

            else:
                x.append([d.id, d.file_path])
            

        print(tabulate(x, headers=head))
        
    def print_chronology(self, option = 'tag'):
        '''Function that lists the experiments in chronological order'''
    
        experiment_list = self.experiments_v2.values()
        counter = 0
        if option == 'files':

            flattened_experiment_list = chain(*experiment_list)
            flattened_experiment_list = [experiment for experiment in flattened_experiment_list]
            flattened_experiment_list.sort(key=lambda x: x.date_time)

            for experiment in flattened_experiment_list:
                cycles = self.count_cycle(experiment.file_path)

                if cycles[0] > counter:
                    counter = cycles [0]
                    print(f'\nCycle number {cycles[0]}\n')

                if len(cycles) > 1 and cycles[1] == 1:
                    print(f'\nSubcycle type: {type(experiment).__name__}\n')
                print(experiment.file_path)
        else:
  
            first_experiment_list = [experiments[0] for experiments in experiment_list]
            first_experiment_list.sort(key=lambda x: x.date_time)
            total_duration = first_experiment_list[-1].date_time - first_experiment_list[0].date_time

            for experiment in first_experiment_list:
                print(f'{experiment.tag}')
            print(f'Total duration: {total_duration}')

    def count_cycle(self, file_path:str):
            """Helper function for for print_chronology.
            Returns the cycle based on file_path
            
            - `file_path`: filepath of an experiment object
            """

            matches = re.findall(r'_(#\d+)', file_path)
            matches = [int(m.strip('#')) for m in matches]
            return matches if matches else [0]

    def print_current_status(self):
        """Helper function to display the current number loaded experiments"""
        try:
            total_number_of_exps = len(tuple(chain(*self.experiments_v2.values())))
            filtered_number_of_exps = len(tuple(chain(*self.filtered.values())))
        except:
            pass
        print(f'Total number of experiments: {total_number_of_exps}. Filtered: {filtered_number_of_exps}')
        try:
            for key, filter in self.last_filter.items():
                if filter is not None:
                    print(key,':', filter)
        except:
            pass



    def batch_process_selected_experiments(self, experiment_collectible = None, **kwargs):
        
        tmp = {}
        if experiment_collectible == None:
            experiment_collectible = self.experiments_v2

        if isinstance(experiment_collectible, dict):
            for experiment_keys, experiments in experiment_collectible.items():
                parameters = []
                for experiment in experiments:
                    experiment.load_data()
                    experiment.process_data()
                    try:
                        parameters.append(experiment.get_parameter_dict())
                        print(parameters)
                    except:
                        print(f'No parameters found for {experiment.file_path}')
                tmp[experiment_keys] = pd.DataFrame.from_records(parameters)
            
            return experiment_collectible
            #return pd.DataFrame.from_records(parameters)
            #return pd.DataFrame(parameters)
            #return experiment_collectible

    def chrono_lsv(self, **kwargs):
        result = self.filter_experiments(name=['HER', 'CHRONOP'])
        self.batch_process_selected_experiments(result)


    def visualize_ECSA(self):
        manager = plt.get_current_fig_manager()
        screen_size = manager.window.winfo_screenwidth(), manager.window.winfo_screenheight()
        plt.close('all')

        width_factor, height_factor = 0.8, 0.6  # 80% width, 60% height
        fig_width = screen_size[0] * width_factor / 100  # Convert pixels to inches
        fig_height = screen_size[1] * height_factor / 100
                
        result = self.filter_experiments(object_type=ECSA)
        print(result)
        processed_data = self.batch_process_selected_experiments(result)
        number_of_subplots = len(processed_data.keys())
        fig, axes = plt.subplots(3,number_of_subplots, figsize=(fig_width, fig_height))

        for number, ((name, cycle, object_type), experiments) in enumerate(processed_data.items()):
 
            for experiment in experiments:
                for j, df in enumerate(experiment.data_list):

                    if number_of_subplots == 1:
                        to_plot = axes[j]
                    else:
                        to_plot = axes[j][number]
                    to_plot.plot(df['E vs RHE'], df['J_GEO'], label=f'{experiment.file_path}')
                    if j+1 == len(experiment.data_list):
                        to_plot.set_xlabel("E vs RHE")
                    else:
                        to_plot.set_xticks([])
                    if number == 0:
                        to_plot.set_ylabel("J_GEO")
        plt.tight_layout()
        plt.show()


    def get_raport_parameters(self):
        
        x = self.filter_experiments(name = ['HER', 'ECSA', 'CHRONOP'])
        self.batch_process_selected_experiments(x)
        for (name, cycle, object_type), experiments in x.items():
            for experiment in experiments:
                if not hasattr(experiment, 'data_list'):
                    experiment.load_data()
                    experiment.process_data()
                x =  experiment.get_parameter_dict()
                for key, items in x.items():
                    print(key, items)
                

    
