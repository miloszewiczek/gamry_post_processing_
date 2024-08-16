#Tutaj wrzucamy wszystkie prerequisites typu stringi/wartości stałe

import gamry_parser
from math import pi
from tkinter.filedialog import askdirectory

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
        
        function()

        print(f'Ended working on {experiment}')
    
    return status()


def print_hello():
    print('Hello')



class Experiment:
    def __init__(self, experiment_type):
        self.experiment_type = experiment_type
        self.experiment_data = None

def LoadFile():
    DTA_file = DTA_Parser.load('test_file.DTA')
    File_Header = DTA_Parser.get_header()
    Experiment_TAG = File_Header['TAG']
    exp = Experiment(experiment_type=Experiment_TAG)
    setattr(exp, 'elo', 'naura')
    print(exp.elo)
    return 

