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


def calculate_slopes(data, start_potential, step, overlap, name='Sample'):
    """Calculate Tafel slopes over segments of the data."""

    def interactive_selection(x_data, y_data, name='Sample'):
        """Fallback interactive plotting when automatic range fails."""
        fig, ax = plt.subplots(figsize=(15, 10))
        ax.scatter(x_data, y_data)
        ax.set_xlabel('log10 j [A/cm2]')
        ax.set_ylabel('E_iR vs RHE [V]')
        ax.set_title(name)

        clicked_points = []

        def on_click(event):
            if event.inaxes != ax:
                return
            clicked_points.append((event.xdata, event.ydata))
            ax.plot(event.xdata, event.ydata, 'ro')
            fig.canvas.draw()

            if len(clicked_points) == 2:
                x1, _ = clicked_points[0]
                x2, _ = clicked_points[1]
                idx1, idx2 = sorted([(np.abs(x_data - x1)).argmin(),
                                    (np.abs(x_data - x2)).argmin()])
                selected_y = y_data[idx1:idx2 + 1]
                mean_val = np.mean(selected_y)
                print(f"Selected x range: {x_data[idx1]:.3f} - {x_data[idx2]:.3f}")
                print(f"Mean y: {mean_val:.5f}")
                ax.axvspan(x_data[idx1], x_data[idx2], color='orange', alpha=0.3)
                plt.title(f"Mean y = {mean_val:.5f}")
                fig.canvas.draw()
                fig.canvas.mpl_disconnect(cid)
                

        cid = fig.canvas.mpl_connect('button_press_event', on_click)
        plt.show()

    
    x_data = np.array(data['E_iR vs RHE [V]'])
    y_data = np.array(data.get('log10 J_GEO [A/cm2]', data.get('log10 J_ECSA [A/cm2]')))

    results = []
    current_potential = start_potential

    while True:
        i_start = (np.abs(x_data - current_potential)).argmin()
        new_potential = x_data[i_start] + step
        idx = (np.abs(x_data - new_potential)).argmin()

        if idx <= i_start or new_potential < min(x_data):
            # Optionally call interactive fallback
            df = pd.DataFrame(results)
            print('Finished!')
            
            break

        # Fit slope
        x_segment = y_data[i_start:idx]
        y_segment = x_data[i_start:idx]
        slope, intercept = np.polyfit(x_segment, -y_segment, 1)
        avg_current = np.mean(x_segment)

        results.append((avg_current, slope))

        # Move to next window
        current_potential = new_potential - overlap
        if current_potential <= min(x_data):
            break

    df = pd.DataFrame(results)
    print(df)
    interactive_selection(df[0], df[1], name)

    return results