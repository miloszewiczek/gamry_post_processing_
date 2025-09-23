from experiments import ECSA
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt

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
        if step == overlap:
            print('Overlap is the same as step, aborting')
            return
        
        x = []
        y = []
        current_potential = start_potential

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
            avg_current = np.mean(x_segment)

            x.append(avg_current)
            y.append(slope)

            # Move to next window
            current_potential = new_potential - overlap
            if current_potential <= min(x_data):
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

            selected_y = y_data[idx1:idx2 + 1]
            ax.axvspan(x_data[idx1], x_data[idx2], color='orange', alpha=0.3)

            if normal_mode is True:
                selected_x = x_data[idx1:idx2+1]
                slope, intercept = np.polyfit(selected_x, selected_y, 1)
                plt.title(f"Slope: {slope:.5f} V/dec")
                result = slope
            
            elif normal_mode is False:
                mean_val = np.mean(selected_y)
                plt.title(f"Mean y = {mean_val:.5f} V/dec")
                result = mean_val
            
            
            canvas.draw()
            canvas.mpl_disconnect(cid)
            if callback:
                callback(result)

    cid = canvas.mpl_connect('button_press_event', on_click)

