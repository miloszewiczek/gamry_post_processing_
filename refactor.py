import defines_refactor
import os

manager = defines_refactor.ExperimentManager()
files = os.listdir('input/')

for file in files:
    experiment = defines_refactor.create_experiment(f'input/{file}', manager)
    #Experiments = manager.get_experiments_by_type(defines_refactor.OpenCircuit)

exp = manager.get_experiments_by_type(defines_refactor.ECSA)
defines_refactor.ECSA_difference(exp, -0.05)




