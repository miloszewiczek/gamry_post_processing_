from experiments import ECSA
import pandas as pd
import numpy as np
from scipy.stats import linregress
from gui.functions import variable_separation
from matplotlib import pyplot as plt
import xarray as xr

def calculate_ECSA_from_slope(ECSA_experiments: list[ECSA], potential_list:list, index, *args, **kwargs) -> list:
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
            
            # difference and integral are mean values of all curves in an experiment. Need to let user know!
            difference = experiment.calculate_difference_at_potential(potential, index = index)
            integral = experiment.calculate_CDL_integral(index = index)
            scanrate = experiment.meta_data['SCANRATE'] / 1000
            
            difference_list.append((scanrate, difference, integral))
        
        # this needs to be changed into results with concat
        tmp_df1 = pd.DataFrame(difference_list, columns = ['Scanrate [V/s]', 'Difference [A]', 'Difference Integrate [A]'])
        tmp_df1 = tmp_df1.sort_values(by = ['Scanrate [V/s]'])
        tmp_df1.reset_index(drop = True, inplace = True)
        

        slope1, intercept1, r_value1, p_value1, std_err1 = linregress(tmp_df1.iloc[:,0], tmp_df1.iloc[:,1])
        slope2, intercept2, r_value2, p_value2, std_err2 = linregress(tmp_df1.iloc[:,0], tmp_df1.iloc[:,2])
        line_x = tmp_df1.iloc[[0, -1]]['Scanrate [V/s]']

        # for plotting/copying the line used for linear regression
        line_y = line_x * slope1 + intercept1
        line_y_int = line_x * slope2 + intercept2
        tmp_df2 = pd.DataFrame({'Line x [V/s]': line_x, 'Line y [A]': line_y, 'Line y Integrate [A]': line_y_int})
        tmp_df2.reset_index(drop = True, inplace = True)

        # joining the dataframes so that it first 3 columns are scanrate/difference/difference_integrate
        # and the other 3 are for plotting the line        
        final_df = pd.concat([tmp_df1, tmp_df2], axis = 1)
        
        results.append(final_df)
        
    return (slope1, intercept1, r_value1), (slope2, intercept2, r_value2), final_df


def calculate_slopes(data, start_potential, step, overlap, normal_mode = True):
    """Calculate Tafel slopes over segments of the data."""

    try:
        x_data = np.array(data['E_iR vs RHE [V]'])
        y_data = np.array(data.get('log10 J_GEO [A/cm2]', data.get('log10 J_ECSA [A/cm2]')))
    except:
        x_data = np.array(data['E vs RHE [V]'])
        y_data = np.array(data['log10 J_GEO [A/cm2]'])

    if normal_mode is True:
        return y_data, x_data
    
    elif normal_mode is False:
        if abs(step) <= abs(overlap):
            print('Overlap is the same as step, aborting')
            return
        
        x = []
        y = []
        current_potential = start_potential

        maximum_steps = 2000
        while True:
            i_start = (np.abs(x_data - current_potential)).argmin()
            new_potential = x_data[i_start] + step
            idx = (np.abs(x_data - new_potential)).argmin()

            if idx <= i_start or new_potential < min(x_data):
                # Optionally call interactive fallback
                print('Finished!')
                break

            # Fit slope
            x_segment = y_data[i_start:idx]
            y_segment = x_data[i_start:idx]
            slope, intercept = np.polyfit(x_segment, -y_segment, 1)
            avg_current = np.mean(x_segment) #this is a logarithm

            #unlogarithming this
            new_avg_current = 10**(avg_current)


            x.append(new_avg_current)
            y.append(slope)

            # Move to next window
            current_potential = new_potential - overlap
            if current_potential <= min(x_data):
                break
            maximum_steps -= 1
            if maximum_steps == 0:
                print('Broken. Attempting to break out of while loop')
                break
        return x, y



def interactive_selection(ax, canvas, x_data, y_data, normal_mode, callback = None):

    clicked_points = []

    def on_click(event):
        if event.inaxes != ax:
            return
        clicked_points.append((event.xdata, event.ydata))
        ax.plot(event.xdata, event.ydata, 'ro')
        canvas.draw()

        if len(clicked_points) == 2:
            x1, _ = clicked_points[0]
            x2, _ = clicked_points[1]

            idx1, idx2 = sorted([
                np.nanargmin(np.abs(x_data - x1)),
                np.nanargmin(np.abs(x_data - x2))
            ])
            selected_x = x_data[idx1:idx2+1]
            selected_y = y_data[idx1:idx2 + 1]
            ax.axvspan(x_data[idx1], x_data[idx2], color='orange', alpha=0.3)

            #d1, d2 and d3 are used for copying later on in tafel.py
            d1 = pd.DataFrame({'x_data': x_data, 
                           'y_data': y_data})
            d2 = pd.DataFrame({'selected_x': selected_x,
                           'selected_y': selected_y})
            d1.reset_index(drop=True, inplace = True)
            d2.reset_index(drop = True, inplace = True)

            if normal_mode is True:

                slope, intercept = np.polyfit(selected_x, selected_y, 1)
                plt.title(f"Slope: {slope:.5f} V/dec")
                
                line_y = np.array(selected_x) * slope + intercept
                line_y = [line_y[0], line_y[-1]]
                d3 = pd.DataFrame({'line_x': [selected_x[0], selected_x[-1]],
                                   'line_y': line_y})

            
            elif normal_mode is False:
                slope = np.mean(selected_y)
                plt.title(f"Mean y = {slope:.5f} V/dec")
                d3 = pd.DataFrame({'line_x': [selected_x[0], selected_x[-1]],
                                    'line_y': [slope, slope]})

            d3.reset_index(drop = True, inplace = True)                
            tmp_df = pd.concat([d1,d2,d3],axis = 1)
            result = slope, tmp_df

            canvas.draw()
            canvas.mpl_disconnect(cid)
            if callback:
                callback(result)

    cid = canvas.mpl_connect('button_press_event', on_click)


def calc_closest(point, array, n = 1) -> int | list[int]:
    """Get closest indexes of an array-like variable to a point. The number of indexes returned is determined by the n variable.

    Args:
        point(float): The point around which the indexing is made.
        array(array-like): Array-like variable from which indexing is made.
        n(int): The number of closest indexes.

    Returns:
        indices(int | list[int]): Index or list of indexes closest to the point in an array.
    """
    
    array = np.asarray(array, dtype = float)
    distances = np.abs(array - point)
    indices = np.argsort(distances)
    indices = indices[~np.isnan(distances[indices])]
    
    if n == 1:
        return indices[:n][0]
    elif n > 1:
        return indices[:n]
    
def calc_first(point, array, n = 1) -> int | list[int]:
    
    mask = array <= point
    array_to_evaluate = array[mask]    
    
    if array.iloc[-1] < array.iloc[0]:
        condition = 0
    elif array.iloc[-1] > array.iloc[0]:
        condition = -1
    try:
        result = array_to_evaluate.index[condition]
    except:
        result = np.nan
    return result


def calc_closest_value(list_of_points:list[float | int], index_array, value_array, mode = 'closest') -> list[float]:
    """Function that calculates the overpotentials to achieve current based on potential-current data.

    Args:
        currents(list): List of currents which are used to calculate the overpotenials.
        x(array-like): Array from which the indexes are calculated.
        y(array-like): Array from which the values are returned.

    Returns:
        overpotentials(list): 
    """
    if mode == 'closest':
        func = calc_closest
    elif mode == 'first':
        func = calc_first

    values = []
    for point in list_of_points:

        index = func(point, index_array, n = 1)
        #if out of bounds
        if not isinstance(index, type(np.nan)):
            value = value_array[index]
        else:
            value = index
        values.append(value)
    return values


def calcualte_overpotentials(benchmark_currents, experiments):
    benchark_currents = variable_separation(benchmark_currents, ',', float)
    #divide to obtain A/cm2
    benchark_currents = [current/1000 for current in benchark_currents]
    columns = ['E_iR vs RHE [V]', 'J_GEO [A/cm2]']
    x = []
    for exp in experiments:

        #need to fix get_columns because curves parameter is now in it
        df = exp.get_columns(curve = 0, columns = columns)
        potentials = df.iloc[:,0]
        current = df.iloc[:,1]
        c = pd.DataFrame([calc_closest_value(benchark_currents, current, potentials, mode = 'first')], index = [exp.file_name], columns = benchark_currents)
        x.append(c)
    x = pd.concat(x)
    x_transf = x.T
    x_transf['mean'] = x_transf.mean(axis = 1)
    x_transf['std'] = x_transf.std(axis = 1)
    return x_transf
