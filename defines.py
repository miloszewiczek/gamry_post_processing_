#Tutaj wrzucamy wszystkie prerequisites typu stringi/wartości stałe

import gamry_parser
from math import pi
from tkinter.filedialog import askdirectory
import os
from glob import glob
import re
import numpy as np



DTA_Parser = gamry_parser.GamryParser()
Experiments = {}

class stale:
    pi_constant = pi
    specific_capacitance = 0.035
    uncompensated_resistance = 0
    reference_electrode_potentials = {"Ag/AgCl":0.21,
                                      "Ag+/Ag": 0.35}
    
class prompts:
    electrode_area_prompt = 'Please enter the electrode area in [cm2]'
    uncompensated_resistance_Ru_prompt = 'Please enter the Ru value in [Ohm]'
    reference_electrode_offset_prompt = 'Please enter the potential of refernece electrode in [V]'
    units_set_prompt = 'Please enter the unit for current and potential'
    ECSA_potential_prompt = 'Please enter the potential for calculating the ECSA in [mV]'

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
        print(f"Modifying {obj.Experiment_TAG}...")
        
        # Wywołanie oryginalnej funkcji
        result = func(obj, *args, **kwargs)
        
        # Po modyfikacji
        print(f"Modyfying {obj.Experiment_TAG}...DONE")
        
        return result
    return wrapper

    
    
        

class Experiment:
    def __init__(self, header, data, cycle_number):
        
        self.Header = header
        self.Data = data
        self.Cycle_number = cycle_number
    
    def Modify_Dataframes(self, Geometric_Area, Reference_electrode_potential):
        '''Depending on the TAG of the experiment, different data modifications are performed'''

        match self.Experiment_TAG:
            case "HER" | "OER" | "CHRONOP" | "CHRONOA" | "STABILITY" | "ECSA":
                for DataDataframe in self.Data:
                    DataDataframe.rename(columns={'Im': 'i', 'Vf': 'E vs REF'}, inplace=True)
                    DataDataframe.loc[:, 'J(GEOMETRIC)'] = DataDataframe['i']/Geometric_Area
                    DataDataframe.loc[:, 'E(iR) vs RHE'] = DataDataframe['E vs REF'] + Reference_electrode_potential - DataDataframe['i']* stale.uncompensated_resistance
                    DataDataframe_modified = DataDataframe[['i', 'E vs REF', 'E(iR) vs RHE']]
                    if self.Experiment_TAG == 'STABILITY' or "CHRONOP":
                        DataDataframe_modified['T'] = DataDataframe['T']
            
            case 'EIS':

                for DataDataframe in self.Data:
                    DataDataframe.rename(columns={'Zreal':'Z','Zimag': 'Z\''})
                    DataDataframe_modified = DataDataframe[['Zreal','Z\'']]
        
    def Double_Layer_Capacitance_Integral(self, Geometric_Area, Scan_Rate):
        '''When the TAG is ECSA, CDL is calculated via integration and current differences at specified potential'''

        for DataDataframe in self.Data:
            Scan_Rate = self.Header['SCANRATE']
            Potential_Window = abs(self.Header['VINIT'] - self.Header['VLIMIT1'])
            x = DataDataframe.loc[0:400]
            y = DataDataframe.loc[400:]
            
            
            CDL_Integral = np.trapz(abs(x['Im']), x['Vf'])
            print(CDL_Integral)
            CDL_Integral2 = np.trapz(y['Im'], y['Vf'])
            diff = CDL_Integral - CDL_Integral2
            print(diff)
            
        


    def Change_Units(self):
        pass

    def SaveToExcel(self):
        pass

    def PlotToRaport(self):
        pass

def GetFilesFromFolder(folder_path):
        '''A function to get file paths of *.DTA files of a given folder. Also checks for empty files'''

        DTA_files = glob(folder_path + '/*.DTA')
        non_empty_DTA_files = [file for file in DTA_files if os.stat(file).st_size != 0]
        return non_empty_DTA_files

def LoadFile(file_path):
    '''Function to load file from string, creating TAG and list of curves'''

    DTA_Parser.load(file_path)
    File_Header = DTA_Parser.get_header()
    Curves_List = DTA_Parser.get_curves()
    
    #GETS RID OF SINGLE-POINT CURVES (GAMRY SOFTWARE BuG) 
    if len(Curves_List[-1].index) == 1:
        Curves_List = Curves_List[:-1]

    #CHECK CYCLE BASED ON NAME
    Cycle_number = re.search('#[1-9]+_#', file_path)
    if Cycle_number != None:
        Cycle_number = Cycle_number.group(0)[1]
    Exp = Experiment(File_Header,
                     Curves_List,
                     Cycle_number)

    return Exp

    
        

    
    
