from exp_manager import ExperimentManager, ECSA, Experiment, Chronoamperometry, LinearVoltammetry, OpenCircuit, Voltammetry, calculate_ECSA_from_slope, batch_integrate_ECSA, calculate_ECSA_difference, ask_user
import os
from config import messages, config
from datetime import datetime
import numpy as np
import pandas as pd

def testing(type = None, function = None):

    manager = ExperimentManager()
    files = [os.path.join('input/',file) for file in os.listdir('input/') if os.path.isfile(os.path.join('input/',file))]
    for file in files:
        manager.create_experiment(file)
    result = manager.filter_experiments(name = input('Name: '))
    df_tmp = manager.batch_process_selected_experiments(result)
    
    return manager.combine_experiment(df_tmp) 