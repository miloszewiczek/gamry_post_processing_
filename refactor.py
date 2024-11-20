import defines_refactor
import os

manager = defines_refactor.ExperimentManager()
files = os.listdir('input/')

for file in files:
    experiment = defines_refactor.create_experiment(f'input/{file}', manager)
    Experiments = manager.get_experiments_by_type(defines_refactor.Experiment)

manager.batch_Ru(0)
voltametry = manager.get_experiments_by_type(defines_refactor.Voltammetry)[5]
voltametry.load_data()
voltametry.process_data()
voltametry.calculate_difference_at_potential(0.6)
voltametry.calculate_CDL_integral()

