#Tutaj wrzucamy wszystkie prerequisites typu stringi/wartości stałe

import gamry_parser
from math import pi
from tkinter.filedialog import askdirectory
import os
from glob import glob
import re
import numpy as np
from scipy import integrate
import pandas as pd
import openpyxl
import matplotlib.pyplot as plt

DTA_Parser = gamry_parser.GamryParser()

class stale:
    pi_constant = pi
    specific_capacitance = 0.035
    uncompensated_resistance = 0
    reference_electrode_potentials = {"Ag/AgCl":0.21,
                                      "Ag+/Ag": 0.35}
    
class prompts:
    electrode_area_prompt = 'Please enter the electrode area in [cm2]: '
    uncompensated_resistance_Ru_prompt = 'Please enter the Ru value in [Ohm]: '
    reference_electrode_offset_prompt = 'Please enter the potential of refernece electrode in [V]: '
    units_set_prompt = 'Please enter the unit for current and potential: '
    ECSA_potential_prompt = 'Please enter the potential for calculating the ECSA in [mV]: '

class errors:
    float_error = 'Wrong type of input data. Please input float number: '


def Log_Modification(func):
    def wrapper(obj, *args, **kwargs):
        # Przed modyfikacją
        print(f"Modifying {obj.Header['TITLE']}...")
        
        # Wywołanie oryginalnej funkcji
        result = func(obj, *args, **kwargs)
        
        # Po modyfikacji
        print(f"Modyfying {obj.Header['TITLE']}...DONE")
        
        return result
    return wrapper

class Experiment():
    def __init__(self, file_name:str, header, data:list, cycle_number:int) -> object:
        
        self.File_Name = file_name
        self.Header = header
        self.Data = data
        self.Cycle_Number = cycle_number
        self.Collection = None

    def Modify_DataFrames(self, Geometric_Area, Reference_Electrode_Potential):
        '''Depending on the TAG of the experiment, different data modifications are performed'''

        TAG = self.Header['TITLE']
        match TAG:
            case "HER" | "OER" | "CHRONOP" | "CHRONOA" | "STABILITY" | "ECSA" | "LSV":
                for DataDataframe in self.Data:
                    DataDataframe_modified = DataDataframe.copy()
                    DataDataframe_modified.rename(columns={'Im': 'i', 'Vf': 'E vs REF'}, inplace=True)
                    DataDataframe_modified.loc[:, 'J(GEOMETRIC)'] = DataDataframe_modified['i']/Geometric_Area
                    DataDataframe_modified.loc[:, 'E(iR) vs RHE'] = DataDataframe_modified['E vs REF'] + Reference_Electrode_Potential - DataDataframe_modified['i']* stale.uncompensated_resistance
                    DataDataframe_modified = DataDataframe_modified[['E vs REF', 'E(iR) vs RHE', 'i']]

                    if TAG == "STABILITY" or TAG == "CHRONOA" or TAG == 'CHRONOP':
                        DataDataframe_modified.insert(0,'T',DataDataframe['T'])
            
            case 'EIS':

                for DataDataframe in self.Data:
                    DataDataframe.rename(columns={'Zreal':'Z','Zimag': 'Z\''})
                    DataDataframe_modified = DataDataframe[['Zreal','Z\'']]
        

    def Charge_Integral(self) -> float:
        '''A function to calculate the integral from cyclic voltammetry data using trapezoid rule
        
        Args:
        self (Experiment): Header and numerical data, including scan limits and i-E data
        
        Returns:
        Average_Area (Float): A mean of all calculated integrals, equal to charge in coulombs
        '''
        
        Areas_tmp = []

        for DataDataframe in self.Data:

            Potential_Data = DataDataframe['Vf']
            Сurrent_Data = DataDataframe['Im']
            Max_Potential = Potential_Data.idxmax()
            
            Integral_Scan_Forward = np.trapz(abs(Сurrent_Data.loc[:Max_Potential + 1]), Potential_Data.loc[:Max_Potential + 1])
            Integral_Scan_Backward = np.trapz(abs(Сurrent_Data.loc[Max_Potential+1:]), Potential_Data.loc[Max_Potential+1:])   
            Integral_Area = abs(Integral_Scan_Forward - Integral_Scan_Backward)   
            Areas_tmp.append(Integral_Area)
            
        Average_Area = np.mean(Areas_tmp)
        return Average_Area

    def Calculate_Specific_Capacitance(self, Charge_Integral:float , Geometric_Area):
        '''A function to calculate specific capacitance in F/cm2 according to equation:
        Cs = Q/(2*A*Scan_rate*Potential_Window), where Q is calculated with Charge_Integral function
        
        Args:
        - Charge_Integral (Float): The area between the anodic and cathodic scans in cyclic voltammogram, equal to charge in coulombs

        Returns:
        - Specific_Capacitance (Float): The electrical capacitance per unit of electrode area
        '''

        Scan_Rate = self.Header['SCANRATE']
        Potential_Window = abs(self.Header['VINIT'] - self.Header['VLIMIT1'])
        Specific_Capacitance = Charge_Integral/(2 * Geometric_Area * Potential_Window * Scan_Rate)
        
        return Specific_Capacitance

    def Calculate_Current_At_Potential_Columnwise(self, *args):
        '''A function to calculate the difference in current at fixed potentials in non-faraday region.
        An alternative to calculate the specific capacitance.
        Supplying multiple values to this function calculates multiple current differences
        
        Args:
        - *args (List of floats): Potentials at which to calculate the current differences

        Returns:
        - Current_DataFrame (DataFrame): A concatenated DataFrame of all curves in the experiment
        '''

        Columns_Dictionary = {}
        Scan_Rate = self.Header['SCANRATE']
        Potential_1 = self.Header['VINIT']
        Potential_2 = self.Header['VLIMIT1']

        
        for Calculation_Potential in args:
            i = 0

            for DataDataframe in self.Data:
                Current_Potential_Data = DataDataframe[['Vf','Im']]
                assert (Calculation_Potential <= max(Potential_1, Potential_2)) and (Calculation_Potential >= min(Potential_1, Potential_2)), "The provided potential to calculate difference in currents is out of range"
                Currents = Current_Potential_Data.iloc[(Current_Potential_Data['Vf']-Calculation_Potential).abs().argsort()[:2]]
                Currents = Currents.diff()
                Currents = Currents.iloc[-1,-1]


                key = (Calculation_Potential, i)
                Columns_Dictionary[key] = Currents
                i += 1

            Current_DataFrame = pd.DataFrame(Columns_Dictionary, index = [Scan_Rate])
            Current_DataFrame.columns = pd.MultiIndex.from_tuples(Current_DataFrame.columns, names = ["POTENTIAL [V]", "CURVE [-]"])
            Current_DataFrame=Current_DataFrame.rename_axis('SCANRATE')
 
        return Current_DataFrame


    def Change_Units(self):
        pass

    def SaveToExcel(self):
        pass

    def PlotToRaport(self):
        pass

class Experiment_Collection():
    '''A general class for storing multiple experiments. Created by Collection_Manager class'''

    def __init__(self, cycle_number):

        self.Experiments = {}
        self.Cycle_Number = cycle_number
        self.Uncompensated_Resistance = 0
        self.Reference_Electrode_Potential = 0
        self.Geometric_Area = 1

    def Add_Experiment(self, experiment):
        if experiment.Header['TITLE'] not in self.Experiments.keys():
            self.Experiments[experiment.Header['TITLE']] = []
        self.Experiments[experiment.Header['TITLE']].append(experiment)
        experiment.Collection = self

    def Set_Uncompensated_Resistance(self):

        try:
            self.Uncompensated_Resistance = float(input(prompts.uncompensated_resistance_Ru_prompt))
        except ValueError:
            print(errors.float_error)
            self.Set_Uncompensated_Resistance()
        else:
            print('Set uncompensated resistance to: ', self.Uncompensated_Resistance, ' for cycle ', self.Cycle_Number)
    
        return self.Uncompensated_Resistance

    def Join_ECSA_DataFrames_Columnwise(self, *args):
        '''A function to evaluate all ECSA experiments and join multiple ECSA dataframes into one.
        Needs a Dataframe with calculated current differences.'''

        ECSA_DataFrame = pd.DataFrame()
        for ECSA_Experiment in self.Experiments["ECSA"]:
            Single_DataFrame = ECSA_Experiment.Calculate_Current_At_Potential_Columnwise(*args)
            ECSA_DataFrame = pd.concat([ECSA_DataFrame, Single_DataFrame])
        
        return ECSA_DataFrame
    
    def Filter_ECSA_DataFrame(self, DataFrame, Potential = None, Curve = None, Scan_Rate = None):
        '''
        Filters the ECSA DataFrame according to given criteria.

        Args:
        - DataFrame (DataFrame): Data to filter
        - Potential (float or None): Potential value to filter. If none, the function returns all potentials
        - Curve (list or None): Curve to filter. If none, the function returns all curves
        - Scanrate (int or list or None): Scan_Rate value or list of values to filter. If none, the function returns all ScanRates

        Returns:
        - DataFrame: Filtered DataFrame
        '''
        
        #Potential filtering
        if Potential is not None:
            if isinstance(Potential, list):
                DataFrame = DataFrame.loc[:, DataFrame.columns.get_level_values('POTENTIAL [V]').isin(Potential)]
            else:
                DataFrame = DataFrame.xs(Potential, level="POTENTIAL [V]", axis=1)
        
        #Curve filtering
        if Curve is not None:
            if isinstance(Curve, list):
                DataFrame = DataFrame.loc[:, (slice(None), Curve)]
            else:
                DataFrame = DataFrame.xs(Curve, level="CURVE [-]", axis=1)
        
        #ScanRate filtering
        if Scan_Rate is not None:
            DataFrame = DataFrame.loc[Scan_Rate]

        return DataFrame

    def Calculate_CDL_From_Slope(self, Filtered_DataFrame):
        '''A function to all possible slopes from Filtered_DataFrame according to linear regression.

        Args:
        - Filtered_DataFrame (DataFrame): Filtered and sorted DataFrame

        Returns:
        - DataFrame: A DataFrame containing linear regression parameters
        '''

        Regression_Results = Filtered_DataFrame.apply(self.Linear_Regression)
        return Regression_Results
    
    def Linear_Regression(self, Series):
        '''Helper function for calculating the linear regression parameters'''
        x = Series.index.values
        return np.polyfit(x, Series, 1)
    
    def Process_Other_DataFrames(self):
        self.Modified_Experiments = {}
        for TAG, Exp in self.Experiments.items():
            if TAG == "ECSA":
                continue
            else:
                self.Modified_Experiments[TAG] = Exp.Modify_DataFrames(Reference_Electrode_Potential = self.Reference_Electrode_Potential,
                                                Geometric_Area = self.Geometric_Area)

        

class Collection_Manager():
    def __init__(self):
        self.Collections = []
    
    def Add_Experiment(self, experiment):

        Matching_Collection = None

        for Collection in self.Collections:
            if Collection.Cycle_Number == experiment.Cycle_Number:
                Matching_Collection = Collection
                break

        if Matching_Collection is None:
            New_Collection = Experiment_Collection(cycle_number = experiment.Cycle_Number)
            self.Collections.append(New_Collection)
            New_Collection.Add_Experiment(experiment)
        elif Matching_Collection:
            Matching_Collection.Add_Experiment(experiment)

    def Get_Collections(self) -> list:
        return self.Collections
    def List_Collections(self):
        for x in self.Collections:
            print(f"Collection number: {x.Cycle_Number}")
            for experiment, number_of_experiments in x.Experiments.items():
                print("\t", experiment, "-", len(number_of_experiments), "files")
            print("")

    def Set_Global_Parameter(self):
        print('''What parameter to set globally - for every collection?
              1. Uncompensated resistance - Ru
              2. Geometric area
              3. Reference electrode potential shift''')
        

            

def GetFilesFromFolder(folder_path):
        '''A function to get file paths of *.DTA files of a given folder. Also checks for empty files'''

        DTA_files = glob(folder_path + '/*.DTA')
        non_empty_DTA_files = [file for file in DTA_files if os.stat(file).st_size != 0]
        return non_empty_DTA_files

def LoadFile(File_Path):
    '''Function to load file from string, creating TAG and list of curves'''

    DTA_Parser.load(File_Path)
    File_Header = DTA_Parser.get_header()
    Curves_List = DTA_Parser.get_curves()
    
    #GETS RID OF SINGLE-POINT CURVES (GAMRY SOFTWARE BuG) 
    if len(Curves_List[-1].index) == 1:
        Curves_List = Curves_List[:-1]

    #CHECK CYCLE BASED ON NAME
    Cycle_number = re.search('#[1-9]+_#', File_Path)
    if Cycle_number != None:
        Cycle_number = Cycle_number.group(0)[1]
    Exp = Experiment(File_Path,
                     File_Header,
                     Curves_List,
                     Cycle_number)

    return Exp

    
        

    
    
