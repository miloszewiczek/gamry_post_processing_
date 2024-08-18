#Tutaj wrzucamy wszystkie prerequisites typu stringi/wartości stałe

import gamry_parser
from math import pi
from tkinter.filedialog import askdirectory
import os
from glob import glob
import re

DTA_Parser = gamry_parser.GamryParser()
Experiments = []

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


def print_hello():
    print('Hello')




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
    def __init__(self, tag, data, cycle_number):
        
        self.Experiment_TAG = tag
        self.Data = data
        self.Cycle_number = cycle_number
    
    def Modify(self):
        '''Depending on the TAG of the experiment, different data modifications are performed'''
        Exp_Tag = self.Experiment_TAG
        match Exp_Tag:
            
            case "HER" | "OER":
                #Modifications
                pass
            
            case "ECSA" | "Electrochemical Surface Area":
                
                print('Jestem ECSA, Co mam zrobić?')

            case "CHRONOA":
                pass
        pass

    def ChangeUnits(self):
        pass

    def SaveToExcel(self):
        pass

    def PlotToRaport(self):
        pass

def GetFilesFromFolder(folder_path):
    '''A function to get file paths of *.DTA files of a given folder. Also checks for empty files'''

    DTA_files = glob(folder_path + '/*.DTA')
    non_empty_DTA_files = [file for file in DTA_files if os.stat(file).st_size != 0]
    print(non_empty_DTA_files)
    return non_empty_DTA_files

def LoadFile(file_path):
    '''Function to load file from string, creating TAG and list of curves'''

    DTA_Parser.load(file_path)
    File_Header = DTA_Parser.get_header()
    Curves_List = DTA_Parser.get_curves()
    Experiment_TAG = File_Header['TITLE']


    #CHECK CYCLE BASED ON NAME
    Cycle_number = re.search('#[1-9]+_#', file_path)
    if Cycle_number != None:
        Cycle_number = Cycle_number.group(0)[1]
    Exp = Experiment(Experiment_TAG,
                     Curves_List,
                     Cycle_number)
    
    #Appends the tag to a global variable to avoid iterating over every object in next steps
    Experiments.append(Experiment_TAG)

    return Exp

    
        

    
    
