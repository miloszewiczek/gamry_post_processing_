import gamry_parser
import pandas as pd
from tabulate import tabulate
import numpy as np
from itertools import chain
from datetime import datetime
import re
from collections import defaultdict
import os
from functools import wraps
import matplotlib.pyplot as plt
from config import config, messages
from openpyxl import Workbook, load_workbook
from collections import defaultdict

DTA_parser = gamry_parser.GamryParser()




 

    
def calculate_ECSA_difference(ECSA_experiments: dict, potential_list:list , calc_eis: bool = False, DifferenceTable = True, *args):
    """A function to compare the ECSA values obtained via the line and integral method.
    Work in progress to find the way to compare multiple potentials. As of now, only one
    potential is accepted. Additionally, functionality with EIS needs to be implemented.
    
    Args:
    ECSA_experiments: the list of ECSA objects to perform the analysis,
    *args: the potentials at which to calculate the CDL using the line method
    
    Returns:
    result: the smallest difference between the CDL values obtained via the two methods
    """
    df_tmp = []
    full_data = []
    if calc_eis == True:
        EIS_CDL = float(input('Jaki CDL z dopasowania?\n'))
    for experiment_keys, experiments in ECSA_experiments.items():
        
        if potential_list == 'STEPSIZE':
            meta_data = experiments[0].load_data()
            step = meta_data['STEPSIZE']/1000
            limit1 = meta_data['VLIMIT1']
            limit2 = meta_data['VLIMIT2']
            potential_array = np.arange(min(limit1,limit2), max(limit1,limit2),step=step)
            CDL_linear_slopes = calculate_ECSA_from_slope(experiments, potential_list = potential_array, *args)
        elif isinstance(potential_list, int):
            potential = potential_list
            CDL_linear_slopes = calculate_ECSA_from_slope(experiments, potential_list = potential, *args)
        else:
            CDL_linear_slopes = calculate_ECSA_from_slope(experiments, potential_list = potential_list, *args)

        '''
        CDL_integrals = batch_integrate_ECSA(experiments)
    
        if DifferenceTable == True:
            table = []
            for integral in CDL_integrals:
                row = []
                for linear_slope in CDL_linear_slopes:
                    
                    if calc_eis == True:
                        result = abs(integral - EIS_CDL)
                    else:
                        result = abs(integral - linear_slope)
                    row.append(result)
                table.append(row)
            
            roznice = np.abs(np.array(CDL_integrals) - EIS_CDL)
            indeks_min = np.argmin(roznice)
            integral_closest = indeks_min

            roznice = np.abs(np.array(CDL_linear_slopes) - EIS_CDL)
            indeks_min = np.argmin(roznice)
            slopes_closest = indeks_min
            tmp = pd.DataFrame(table)
        
            return tmp, integral_closest, slopes_closest
        else:
            columns = ['integral slope'] + [potential_list]
            #columns = [str(scanrt) for scanrt in range(10,110,10)] + [potential_list]
            row = CDL_linear_slopes[0]
            full_data.append(CDL_linear_slopes[1])
            df = pd.DataFrame([row], columns = columns)
            df_tmp.append(df)
    df_tmp = pd.concat(df_tmp)
    full_data = pd.concat(full_data, axis=1)
    
    return df_tmp, full_data
    '''
        


            



def calculate_tafel_slope_old(data, starting_point, step, overlap, name = 'Sample', curve_number = None, i = None):
    '''
    if i == None:
        output[curve_number] = []

    i_start = (np.abs(data['Vf_iR'] - starting_point)).argmin()
    print("Starting index: ", i_start)
    search = data['Vf_iR'][i_start]
    print("Potential of starting point: ", search)
    new_search = search + step
    print("Potential of new point: ", new_search)
    idx = (np.abs(data['Vf_iR'] - new_search)).argmin()
    print("Finishing index: ", idx)
    if (idx < i_start) or (new_search < min(data['Vf_iR'])):

        fig, ax = plt.subplots(figsize=(15,10))
        plt.xlabel('Average log10 j [mA/cm2]')
        plt.ylabel('Tafel slope [mV/dec]')
        plt.title(name)
        
        print('Calculated finish index is lower than starting index. Aborting. This is due to iR-drop and bubbles detachment.')
        df = pd.DataFrame(output[curve_number], columns = ['E_begining', 'E_final', 'Average current [mA/cm2]', 'Tafel slope [mV/dec]'])
        resulting_dfs.append(df)

        x_data = np.array([seg[2] for seg in output[curve_number]])
        y_data = np.array([seg[3] for seg in output[curve_number]])
        ax.scatter(x_data,y_data)
        ax.set_ylim(0,150)
        clicked_points = []

        
        def on_click(event):
            if event.inaxes != ax:
                return
            
            clicked_points.append((event.xdata, event.ydata))

            # Draw a red dot
            ax.plot(event.xdata, event.ydata, 'ro')
            fig.canvas.draw()

            if len(clicked_points) == 2:
                # Get x-values of clicks
                x1, _ = clicked_points[0]
                x2, _ = clicked_points[1]

                # Find closest indices
                idx1 = (np.abs(x_data - x1)).argmin()
                idx2 = (np.abs(x_data - x2)).argmin()

                i_min, i_max = sorted([idx1, idx2])  # Ensure correct order

                selected_x = x_data[i_min:i_max+1]
                selected_y = y_data[i_min:i_max+1]

                mean_val = np.mean(selected_y)
                print(f"\nSelected range: x = [{x_data[i_min]:.3f}, {x_data[i_max]:.3f}]")
                print(f"Mean y-value in range: {mean_val:.5f}")

                # Optionally shade selected region
                ax.axvspan(x_data[i_min], x_data[i_max], color='orange', alpha=0.3)
                fig.canvas.draw()

                # Disconnect listener so it doesn’t keep listening
                fig.canvas.mpl_disconnect(cid)
                plt.title(f"Mean y = {mean_val:.5f} between selected points")
                fig.canvas.draw()

        # Connect the click event
        cid = fig.canvas.mpl_connect('button_press_event', on_click)
        plt.show()
        

        return df
        '''
    
class Analyzer():
    def __init__(self):
        pass

class Visualizer():
    def __init__(self):
        pass

class Corporator():
    def __init__(self):
        self.loader = ExperimentLoader()
        
if __name__ == "__main__":
    from tkinter import Tk
    from core.visualizer import *
    loader = ExperimentLoader()
    loader.load_testing()
    manager = ExperimentManager()
    manager.list_of_experiments = loader.list_of_experiments 
    manager.filter('HER', 1)
    for exp in manager.filtered:
        exp.load_data()
        exp.process_data()
    '''
    x = manager.filtered
    root = Tk()
    gui = VisualizerWindow(root, x)
    root.mainloop()
    '''
