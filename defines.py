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



def print_current_status_wrapper(experiment, function):

    def status():

        print(f'Beginning to work on {experiment}')
        #Zamiast function zdefiniowanego oddzielnie, można po prostu zdefiniować metodę w klasie Experiment. W ten sposób od razu dostaniemy się do atrybutu TAG i zarazem experiment do wrappera
        function()

        print(f'Ended working on {experiment}')
    
    return status()

def log_modification(func):
    def wrapper(obj, *args, **kwargs):
        # Przed modyfikacją
        print(f"Modifying {obj.Header['TAG']}...")
        
        # Wywołanie oryginalnej funkcji
        result = func(obj, *args, **kwargs)
        
        # Po modyfikacji
        print(f"Modyfying {obj.Header['TAG']}...DONE")
        
        return result
    return wrapper

class Experiment():
    def __init__(self, file_name, header, data, cycle_number):
        
        self.File_Name = file_name
        self.Header = header
        self.Data = data
        self.Cycle_Number = cycle_number
        self.Collection = None

    def Modify_Dataframes(self, Geometric_Area, Reference_electrode_potential):
        '''Depending on the TAG of the experiment, different data modifications are performed'''

        TAG = self.Header['TITLE']
        match TAG:
            case "HER" | "OER" | "CHRONOP" | "CHRONOA" | "STABILITY" | "ECSA" | "LSV":
                for DataDataframe in self.Data:
                    DataDataframe_modified = DataDataframe.copy()
                    DataDataframe_modified.rename(columns={'Im': 'i', 'Vf': 'E vs REF'}, inplace=True)
                    DataDataframe_modified.loc[:, 'J(GEOMETRIC)'] = DataDataframe_modified['i']/Geometric_Area
                    DataDataframe_modified.loc[:, 'E(iR) vs RHE'] = DataDataframe_modified['E vs REF'] + Reference_electrode_potential - DataDataframe_modified['i']* stale.uncompensated_resistance
                    DataDataframe_modified = DataDataframe_modified[['E vs REF', 'E(iR) vs RHE', 'i']]

                    if TAG == "STABILITY" or TAG == "CHRONOA" or TAG == 'CHRONOP':
                        DataDataframe_modified.insert(0,'T',DataDataframe['T'])
            
            case 'EIS':

                for DataDataframe in self.Data:
                    DataDataframe.rename(columns={'Zreal':'Z','Zimag': 'Z\''})
                    DataDataframe_modified = DataDataframe[['Zreal','Z\'']]
        

    def Charge_Integral(self):
        '''When the TAG is ECSA, total charge is calculated via integration of current over potential applied potential'''
        
        Areas_tmp = []

        for DataDataframe in self.Data:

            Potential_Data = DataDataframe['Vf']
            Сurrent_Data = DataDataframe['Im']
            Max_Potential = Potential_Data.idxmax()
            
            Integral_Scan_Forward = np.trapz(abs(Сurrent_Data.loc[:Max_Potential + 1]), Potential_Data.loc[:Max_Potential + 1])
            Integral_Scan_Backward = np.trapz(abs(Сurrent_Data.loc[Max_Potential+1:]), Potential_Data.loc[Max_Potential+1:])   
            Integral_Area = abs(Integral_Scan_Forward - Integral_Scan_Backward)   
            Areas_tmp.append(Integral_Area)

        return np.mean(Areas_tmp)

    def Calculate_Specific_Capacitance(self, Charge_Integral, Geometric_Area):
        '''A function to calculate specific capacitance in F/cm2 according to equation:
        Cs = Q/(2*A*Scan_rate*Potential_Window), where Q is calculated with Charge_Integral function'''

        Scan_Rate = self.Header['SCANRATE']
        Potential_Window = abs(self.Header['VINIT'] - self.Header['VLIMIT1'])
        Specific_Capacitance = Charge_Integral/(2 * Geometric_Area * Potential_Window * Scan_Rate)
        
        return Specific_Capacitance
        
    def Calculate_CDL_From_Slope(self, *args):
        '''A function to calculate the difference in current at fixed potentials in non-faraday region.
        An alternative to calculate the specific capacitance.
        Supplying multiple values to this function calculates multiple current differences'''

        Currents_Rows = []
        Scan_Rate = self.Header['SCANRATE']
        Potential_1 = self.Header['VINIT']
        Potential_2 = self.Header['VLIMIT1']

        for DataDataframe in self.Data:
            
            Currents_Columns = []
            Current_Potential_Data = DataDataframe[['Vf','Im']]

            for Calculation_Potential in args:

                assert (Calculation_Potential <= max(Potential_1, Potential_2)) and (Calculation_Potential >= min(Potential_1, Potential_2)), "The provided potential to calculate difference in currents is out of range"
                Currents = Current_Potential_Data.iloc[(Current_Potential_Data['Vf']-Calculation_Potential).abs().argsort()[:2]]
                Currents = Currents.diff()
                Currents = Currents.iloc[-1,-1]
                Currents_Columns.append(Currents)

            Currents_Rows.append(Currents_Columns)
        
        Index_Names = ['Curve ' + str(i) for i in range(len(self.Data))]
        Column_Names = [str(arg)+' V' for arg in args]
        Current_DataFrame = pd.DataFrame(Currents_Rows, columns = Column_Names, index = Index_Names)
        Current_DataFrame.loc['Mean'] = Current_DataFrame.mean()
        Current_DataFrame.loc['Standard Deviation'] = Current_DataFrame.std()
        Current_DataFrame['SCANRATE'] = self.Header['SCANRATE']
        
        return Current_DataFrame

    def Change_Units(self):
        pass

    def SaveToExcel(self):
        pass

    def PlotToRaport(self):
        pass

class Experiment_Collection():
    def __init__(self, cycle_number):

        self.Experiments = {}
        self.Cycle_Number = cycle_number
        self.Uncompensated_Resistance = None

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
    
    def Join_ECSA_DataFrames(self, *args):

        ECSA_DataFrame = pd.DataFrame()
        for ECSA_Experiment in self.Experiments["ECSA"]:
            Single_Dataframe = ECSA_Experiment.Calculate_CDL_From_Slope(*args)
            ECSA_DataFrame = pd.concat([ECSA_DataFrame, Single_Dataframe])
        multi = pd.MultiIndex.from_arrays([ECSA_DataFrame["SCANRATE"], ECSA_DataFrame.index], names=["SCANRATE","CURVE_NUMERO"])
        ECSA_DataFrame.index = multi
        self.ECSA_DataFrame = ECSA_DataFrame

    def Filter_ECSA_DataFrame(self, **kwargs):
        
        tmp_DataFrame = self.ECSA_DataFrame.copy()

        if "Filtered_Curve" in kwargs:
            Filtered_Curve_name = kwargs["Filtered_Curve"]
            tmp_DataFrame = tmp_DataFrame.xs(Filtered_Curve_name, level = "CURVE_NUMERO")
        
        if "Scanrate" in kwargs:
            Scanrate_threshold = kwargs["Scanrate"]
            tmp_DataFrame = tmp_DataFrame.query(f"{Scanrate_threshold[0]} < SCANRATE < {Scanrate_threshold[1]}")
        
        if "Potential" in kwargs:
            Potential_value = kwargs["Potential"]
            tmp_DataFrame = tmp_DataFrame[Potential_value]
        
        return tmp_DataFrame
    
    def Calculate_CDL_From_Slope(self, **kwargs):

        if 'DataFrame' in kwargs:
            tmp = kwargs["DataFrame"].copy()
        else:
            tmp = self.ECSA_DataFrame.copy()

        print(tmp.index.get_level_values("SCANRATE").tolist())


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
    
    def Print_Showcase(self):
        for coll in self.Collections:
            print(coll.Experiments)

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

    
        

    
    
