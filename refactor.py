import defines_refactor
import os

manager = defines_refactor.ExperimentManager()
files = os.listdir('input/')

for file in files:
    experiment = defines_refactor.create_experiment(f'input/{file}', manager)
    Experiments = manager.get_experiments_by_type(defines_refactor.Experiment)

manager.batch_Ru(5)
manager.list_details()
voltametry = manager.get_experiments_by_type(defines_refactor.Voltammetry)
for x in voltametry:
    x.load_data()
    x.print_potential_path()