#A PIECE OF CODE RELATED TO CREATING WORKFLOWS, EG:
#LOAD FILES => PROCESS THEM (WITH SPECIFIED PARAMTERES) => SAVE THEM
#CUSTOMIZABLE, SO THAT USER CAN CREATE DIFFERNT WORKFLOWS

from core import ExperimentLoader, ExperimentManager
from experiments import ECSA
from functions.functions import calculate_ECSA_from_slope

loader = ExperimentLoader()
files = loader.choose_folder()
manager = ExperimentManager(files)

result = calculate_ECSA_from_slope(manager.filter(object_type = ECSA))
print(result)

