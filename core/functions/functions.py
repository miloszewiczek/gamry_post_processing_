from core.experiments import ECSA
import pandas as pd
import numpy as np
from scipy.stats import linregress
from matplotlib import pyplot as plt
import xarray as xr
import os
import platform
import subprocess



def calculate_ECSA_from_slope(ECSA_experiments: list[ECSA], potential:float, index, *args, **kwargs) -> list:
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

    results = {}
    data = []

    difference_list = []

    for experiment in ECSA_experiments:
        if not hasattr(experiment, 'data_list'):
            experiment.load_all()
            experiment.process_data()
        
        difference = experiment.calculate_difference_at_potential(potential, index=index)
        integral = experiment.calculate_CDL_integral(index=index)
        scanrate = experiment.meta_data['SCANRATE'] / 1000  # mV -> V/s
        
        difference_list.append({
            'Scanrate [V/s]': scanrate, 
            'Difference [A]': difference, 
            'Integral [A]': integral
        })
    
    # Czysty DataFrame z punktami pomiarowymi
    df_data = pd.DataFrame(difference_list).sort_values(by='Scanrate [V/s]').reset_index(drop=True)
    
    # Regresje liniowe
    res_line = linregress(df_data['Scanrate [V/s]'], df_data['Difference [A]'])
    res_line_integrate = linregress(df_data['Scanrate [V/s]'], df_data['Difference [A]'])
    
    df_data['Line fit [A]'] = df_data['Scanrate [V/s]'] * res_line.slope + res_line.intercept
    df_data['Integrate fit [A]'] = df_data['Scanrate [V/s]'] * res_line_integrate.slope + res_line_integrate.intercept
    
    fitting_df = pd.DataFrame([[res_line.slope, res_line.intercept, res_line.rvalue**2]], columns = ['Slope', 'Intercept', 'R^2'])
    fitting_df.reset_index(drop = True, inplace= True)
    results["df_fitting"] = fitting_df
    results["df_data"] = df_data
        
    return results

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
    
def calc_closest_2D(x_data, y_data, click_x, click_y, ax) -> tuple[float,float]:
    # Pobieramy aktualne limity osi
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        
        # Liczymy dystans procentowy (0.0 do 1.0 zasięgu osi)
        dx = (x_data - click_x) / (xlim[1] - xlim[0])
        dy = (y_data - click_y) / (ylim[1] - ylim[0])
        
        idx = np.argmin(dx**2 + dy**2)
        return x_data[idx], y_data[idx]
        
        # Wybieramy indeks tego, który ma najmniejszy dystans
     
def convert_to_overpotential_scale(array, potential):
    return array - potential


def calc_first(point, array, n = 1) -> int | list[int]:
    
    if point < 0:
        mask = array <= point
    elif point > 0:
        mask = array >= point

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



