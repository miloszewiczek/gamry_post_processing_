from experiments import ECSA
import pandas as pd
import numpy as np

def calculate_ECSA_from_slope(ECSA_experiments: list[ECSA], potential_list:list, *args) -> list:
    """Function to perform the calculate_difference_at_potential on
    provided ECSA experiments in different potentials and fit the 
    data to a linear regression model.
    The CDL is calculated as the slope of the function:
    
    di = CDL * v,
    where: di - difference in charging currents, v - scanrate
    
    - `ECSA_experiments`: list of ECSA objects,
    - `potential_list`: an array of potential values to compute the current difference

    Returns:
    - `results`: a list of linear slopes, representing the CDL.
    """

    if isinstance(potential_list, float) or isinstance(potential_list, int):
        potential_list = [potential_list]

    difference_list = []
    results = []

    for potential in potential_list:

        for experiment in ECSA_experiments:
            if not hasattr(experiment,'data_list'):
                experiment.load_data()
            difference = experiment.calculate_difference_at_potential(potential)
            integral = experiment.calculate_CDL_integral()
            scanrate = experiment.meta_data['SCANRATE'] / 1000
            difference_list.append((scanrate, difference, integral))
        x = pd.DataFrame(difference_list)
        
        slope1, intercept = np.polyfit(x.iloc[:,0], x.iloc[:,1], 1)
        slope2, intercept2 = np.polyfit(x.iloc[:,0], x.iloc[:,2],1)
        results.append(x)
        
    return (slope1, slope2), x