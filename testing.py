from exp_manager import ExperimentManager, ExperimentLoader, ECSA, Experiment, Chronoamperometry, LinearVoltammetry, OpenCircuit, Voltammetry, calculate_ECSA_from_slope, calculate_ECSA_difference, ask_user
import os
from config import messages, config
from datetime import datetime
import numpy as np
import pandas as pd

def testing_f():
    loader = ExperimentLoader()
    loader.load_testing()
    manager = ExperimentManager()
    manager.list_of_experiments = loader.list_of_experiments 
    print('Testing ready...')
    return loader, manager

l, m = testing_f()
m.filter('MYCIE')
x = m.filtered[0]
x.load_data()
x.process_data()