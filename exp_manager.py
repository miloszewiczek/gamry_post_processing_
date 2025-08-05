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
from collections import defaultdict

DTA_parser = gamry_parser.GamryParser()
geometrical_area = config['default_settings']['geometrical_area']
reference_potential = config['default_settings']['reference_potential']

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
        
        if len(self.data_list) > 1:
            include_curve_index = True
        else:
            include_curve_index = False

        print(f'Processing data of {self.file_path} with id: {self.id} ({len(self.data_list)} curves).')
        dfs = []
        for  curve_index, curve in enumerate(self.data_list):
            
            processed_curve = self._add_computed_column(curve)

            level_values, level_names = self.get_multiindex_labels(processed_curve.columns, curve_index, add_curve_index = include_curve_index)
            processed_curve.columns = pd.MultiIndex.from_product(level_values, names = level_names)
            dfs.append(processed_curve)
        
        self.processed_data = pd.concat(dfs,axis=1)
        return self.processed_data

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


class LinearVoltammetry(Experiment):
    def __init__(self, file_path, date_time, id, tag, cycle):
        super().__init__(file_path, date_time, id, tag, cycle)
        self.tafel_curves = []
    
    def process_data(self) -> pd.DataFrame:
        
        result = super().process_data()

        return result

    def _add_computed_column(self, curve):
        LSV_curve =  super()._add_computed_column(curve)
        curve['log10 J_GEO [A/cm2]'] = np.log10(0-LSV_curve['J_GEO [A/cm2]'])
        Tafel_curve = pd.concat([curve['log10 J_GEO [A/cm2]'], LSV_curve['E vs RHE [V]']], axis=1)
        self.tafel_curves.append(Tafel_curve)

        return pd.concat([LSV_curve, Tafel_curve], axis=1)

    def get_multiindex_labels(self, columns, curve_index, add_curve_index=True):

        level_values = [[f'{self.file_path}'], columns]
        level_names = ['Path', 'Parameter']
        return level_values, level_names
    
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
        level_names = ['Path', 'Cycle', 'Parameter']
        return level_values, level_names


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
        return 
    
    def get_parameter_dict(self):

        results_dict = {'id': self.id, 'integral': self.integral, 'diff': (self.diff)}
        #return {'Difference(s)': self.diff, 'Integral': self.integral}
        return results_dict
        

class Chronoamperometry(Experiment):
    def __init__(self, file_path, date_time, id, tag, cycle):
        super().__init__(file_path, date_time, id, tag, cycle)
        self.current = None
    
    def process_data(self, interactive = False):

        result = super().process_data()
        if interactive == False:
            self.get_current_at_time(config['default_settings']['time_chrono'])
        elif interactive == True:
            self.pick_current()

        return result
    
    
    def get_multiindex_labels(self, columns, curve_index, add_curve_index = True) -> tuple[list[list[str]], list[str]]:
        """
        Returns levels and names for multiindexing. Is different for each 
        type of experiment.
        Returns:
        - list of lists: values for each level of the Multiindex (e.g. [[path], [curve_name], [column1, column2, column2, ...]])
        - list of level names (e.g. ['Path, 'Curve', 'Metric])
        """
        final_potential = self.meta_data['VSTEP2'] + reference_potential
        final_potential = '{:.2f}'.format(final_potential)

        level_values = [[self.file_path], [final_potential], columns]
        level_names = ['Path', 'E vs RHE [V]', 'Parameter']
        return level_values, level_names

    def _add_computed_column(self, curve:pd.DataFrame) -> pd.DataFrame:

        curve['J_GEO [A/cm2]'] = curve['Im']/geometrical_area
        curve['E vs RHE [V]'] = curve['Vf'] + reference_potential
        curve['T [s]'] = curve['T']

        if hasattr(self, 'Ru'):
            curve['E_iR vs RHE [V]'] = curve['Vf'] + reference_potential - self.Ru * curve['Im']
            return curve[['E vs RHE [V]', 'E_iR vs RHE [V]', 'J_GEO [A/cm2]']]
        
        curve = curve.reset_index(drop=True)

        return curve[['T [s]', 'E vs RHE [V]', 'J_GEO [A/cm2]']]


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
            current = curve.iloc[closest_index]['J_GEO [A/cm2]']
            self.current = current
            return current
        

    def pick_current(self):

        time, potential, current = self.data_list[0]['T'], self.data_list[0]['E vs RHE [V]'], self.data_list[0]['J_GEO [A/cm2]']
        fig, ax = plt.subplots()
        line, = ax.plot(time, current)
        selected_point, = ax.plot([], [], 'ro')
        plt.xlabel("T [s]")
        plt.ylabel("Current density [A/cm2]")
        ax.legend()

        def onclick(event):
            if event.inaxes != ax:
                return
            x_click = event.xdata
            y_click = event.ydata
            distances = np.sqrt((time - x_click)**2 + (current - y_click)**2)
            idx = np.argmin(distances)
            x_sel = time[idx]
            y_sel = current[idx]
            
            pot_iR = potential[idx] - current[idx]

            selected_point.set_data([x_sel], [y_sel])
            fig.canvas.draw()

            # Save point and close plot
            self.time = x_sel
            self.current = y_sel
            self.potential = pot_iR
            plt.close(fig)

        cid = fig.canvas.mpl_connect('button_press_event', onclick)
        plt.show()
        
    def get_parameter_dict(self):

        results_dict = {'id': self.id, 'current': self.current}
        return results_dict
    


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
        results.append(x)
        
    return (slope1, slope2), x
    
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

        '''
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
    '''
        

class ExperimentLoader():
    '''An interface class to aggregate and manage the experiments. '''

    def __init__(self):
        '''All of the experiments are stored in the variable self.experiments'''
        self.experiments = {}
        self.filtered = {}
        self.list_of_experiments = []
        self.experiments_v2 = defaultdict(list)
        
        #Default settings, always implemented in the program
        self.experiment_classes = {
            'IDENTIFIERS':{
                "MYCIE" : Voltammetry,
                #"CHRONOA" : Chronoamperometry,
                #"EIS" : EIS,
                "HER" : LinearVoltammetry,
                "ECSA" : ECSA,
                "Open Circuit Potential": OpenCircuit
                },
            'TAGS':{
                "CV" : Voltammetry,
                "LSV" : LinearVoltammetry,
                "CORPOT" : OpenCircuit,
                "CHRONOA" : Chronoamperometry,
                "EISPOT": EIS
                }
        
        }
        
        self.selected_experiments = None
        self.id_counter = 0


    def load_testing(self):
        
        files = [os.path.join('input/', file) for file in os.listdir('input/') if os.path.isfile(os.path.join('input/', file))]
        for file in files:
            self.create_experiment(file)
        print('Added testing files (input/*)')
        
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
        self.list_of_experiments.append(experiment)

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
            
class ExperimentManager():
    def __init__(self):
        self.atr = None
        self.filtered = None
            
    def combine_experiment(self, experiment_list):
        for experiment in experiment_list:
            return pd.concat(experiment_list, axis=1)
    
    def save_experiment(self, experiment_list:dict[Experiment] = None, file_name = 'test', option = 'last'):


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
    
    
    def filter(
        self,
        name: str | list[str] = None,
        cycle: int | list[int] = None,
        object_type: type | str | list[type | str] = None,
    ) -> list[Experiment]:
        """
        General filter method to select experiments matching all given criteria.

        Args:
            name: single name or list of substrings to match in file_path
            cycle: int or list of ints
            object_type: class, class name, or list of either

        Returns:
            List of Experiment objects matching all filters.
        """
        def name_matches(exp):
            if name is None:
                return True
            if isinstance(name, str):
                return name in exp.file_path
            return any(n in exp.file_path for n in name)

        def cycle_matches(exp):
            if cycle is None:
                return True
            if isinstance(cycle, int):
                return getattr(exp, "cycle", None) == cycle
            return getattr(exp, "cycle", None) in cycle

        def type_matches(exp):
            if object_type is None:
                return True
            types = object_type if isinstance(object_type, list) else [object_type]
            for t in types:
                if isinstance(t, str) and t.lower() in type(exp).__name__.lower():
                    return True
                if isinstance(t, type) and isinstance(exp, t):
                    return True
            return False

        self.filtered = [exp for exp in self.list_of_experiments if name_matches(exp) and cycle_matches(exp) and type_matches(exp)]
        return self.filtered

    
    def filter_by_id(self, id):
        
        if not isinstance(id, list):
            id = [id]

        tmp = []
        tmp2 = {key:None for key in id}

        for experiment in self.filtered:
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
    
        def count_cycle(self, file_path:str):
            """Helper function for for print_chronology.
            Returns the cycle based on file_path
            
            - `file_path`: filepath of an experiment object
            """

            matches = re.findall(r'_(#\d+)', file_path)
            matches = [int(m.strip('#')) for m in matches]
            return matches if matches else [0]


        experiment_list = self.filtered
        counter = 0
        if option == 'files':

            flattened_experiment_list = experiment_list
            flattened_experiment_list.sort(key=lambda x: x.date_time)

            for experiment in flattened_experiment_list:
                cycles = count_cycle(experiment.file_path)

                if cycles[0] > counter:
                    counter = cycles [0]
                    print(f'\nCycle number {cycles[0]}\n')

                if len(cycles) > 1 and cycles[1] == 1:
                    print(f'\nSubcycle type: {type(experiment).__name__}\n')
                print(experiment.file_path)
        else:
  
            first_experiment_list = experiment_list
            first_experiment_list.sort(key=lambda x: x.date_time)
            total_duration = first_experiment_list[-1].date_time - first_experiment_list[0].date_time

            for experiment in first_experiment_list:
                print(f'{experiment.tag}')
            print(f'Total duration: {total_duration}')


    def batch_process_selected_experiments(self, experiment_collectible = None, **kwargs):
        
        tmp = []

        if experiment_collectible == None:
            experiment_collectible = self.filtered

        for experiment in experiment_collectible:
            parameters = []
           
            experiment.load_data()
            experiment.process_data()
            tmp.append(experiment)
            try:
                parameters.append(experiment.get_parameter_dict())
            except:
                print(f'No parameters found for {experiment.file_path}')
            

        x = self.combine_experiment(tmp)
        x.to_excel(input('Name of data to save: ')+'.xlsx', engine='openpyxl')
        return experiment_collectible
        #return pd.DataFrame.from_records(parameters)
        #return pd.DataFrame(parameters)
        #return experiment_collectible


def calculate_tafel_slope(data, starting_point, step, overlap, name = 'Sample', curve_number = None, i = None):
    '''
    if i == None:
        output[curve_number] = []

    i_start = (np.abs(data['Vf_iR'] - starting_point)).argmin()
    print("Starting index: ", i_start)
    search = data['Vf_iR'][i_start]
    print("Potential of starting point: ", search)
    new_search = search + step
    print("Potential of new point: ", new_search)
    idx = (np.abs(data['Vf_iR'] - new_search)).argmin()
    print("Finishing index: ", idx)
    if (idx < i_start) or (new_search < min(data['Vf_iR'])):

        fig, ax = plt.subplots(figsize=(15,10))
        plt.xlabel('Average log10 j [mA/cm2]')
        plt.ylabel('Tafel slope [mV/dec]')
        plt.title(name)
        
        print('Calculated finish index is lower than starting index. Aborting. This is due to iR-drop and bubbles detachment.')
        df = pd.DataFrame(output[curve_number], columns = ['E_begining', 'E_final', 'Average current [mA/cm2]', 'Tafel slope [mV/dec]'])
        resulting_dfs.append(df)

        x_data = np.array([seg[2] for seg in output[curve_number]])
        y_data = np.array([seg[3] for seg in output[curve_number]])
        ax.scatter(x_data,y_data)
        ax.set_ylim(0,150)
        clicked_points = []

        
        def on_click(event):
            if event.inaxes != ax:
                return
            
            clicked_points.append((event.xdata, event.ydata))

            # Draw a red dot
            ax.plot(event.xdata, event.ydata, 'ro')
            fig.canvas.draw()

            if len(clicked_points) == 2:
                # Get x-values of clicks
                x1, _ = clicked_points[0]
                x2, _ = clicked_points[1]

                # Find closest indices
                idx1 = (np.abs(x_data - x1)).argmin()
                idx2 = (np.abs(x_data - x2)).argmin()

                i_min, i_max = sorted([idx1, idx2])  # Ensure correct order

                selected_x = x_data[i_min:i_max+1]
                selected_y = y_data[i_min:i_max+1]

                mean_val = np.mean(selected_y)
                print(f"\nSelected range: x = [{x_data[i_min]:.3f}, {x_data[i_max]:.3f}]")
                print(f"Mean y-value in range: {mean_val:.5f}")

                # Optionally shade selected region
                ax.axvspan(x_data[i_min], x_data[i_max], color='orange', alpha=0.3)
                fig.canvas.draw()

                # Disconnect listener so it doesn’t keep listening
                fig.canvas.mpl_disconnect(cid)
                plt.title(f"Mean y = {mean_val:.5f} between selected points")
                fig.canvas.draw()

        # Connect the click event
        cid = fig.canvas.mpl_connect('button_press_event', on_click)
        plt.show()
        

        return df
        '''
    
class Analyzer():
    def __init__(self):
        pass

class Visualizer():
    def __init__(self):
        pass

class Corporator():
    def __init__(self):
        self.loader = ExperimentLoader()
        
if __name__ == "__main__":
    from tkinter import Tk
    from visualizer import *
    loader = ExperimentLoader()
    loader.load_testing()
    manager = ExperimentManager()
    manager.list_of_experiments = loader.list_of_experiments 
    manager.filter('ECSA', 1)
    for exp in manager.filtered:
        exp.load_data()
        exp.process_data()
    x = manager.filtered
    root = Tk()
    gui = VisualizerWindow(root, x)
    root.mainloop()
