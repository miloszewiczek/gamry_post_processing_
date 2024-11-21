import defines_refactor
import os

manager = defines_refactor.ExperimentManager()
files = os.listdir('input/')

for file in files:
    experiment = defines_refactor.create_experiment(f'input/{file}', manager)
    Experiments = manager.get_experiments_by_type(defines_refactor.Experiment)

manager.batch_Ru(0)

experiment_type = defines_refactor.Chronoamperometry
experiment = manager.get_experiments_by_type(experiment_type)[0]
experiment.load_data()
experiment.get_current_at_time(30)


