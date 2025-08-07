from .base import *


class Chronoamperometry(Experiment):
    def __init__(self, file_path, date_time, id, tag, cycle):
        super().__init__(file_path, date_time, id, tag, cycle)
        self.current = None
    
    def process_data(self, interactive = False):

        result = super().process_data()
        if interactive == False:
            self.get_current_at_time(settings.options['time'])
        elif interactive == True:
            self.pick_current()

        return result
    
    
    def get_multiindex_labels(self, columns, curve_index, add_curve_index = True) -> tuple[list[list[str]], list[str]]:
        """
        Returns levels and names for multiindexing. Is different for each 
        type of experiment.
        Returns:
        - list of lists: values for each level of the Multiindex (e.g. [[path], [curve_name], [column1, column2, column2, ...]])
        - list of level names (e.g. ['Path, 'Curve', 'Metric])
        """
        final_potential = self.meta_data['VSTEP2'] + reference_potential
        final_potential = '{:.2f}'.format(final_potential)

        level_values = [[self.file_path], [final_potential], columns]
        level_names = ['Path', 'E vs RHE [V]', 'Parameter']
        return level_values, level_names

    def _add_computed_column(self, curve:pd.DataFrame) -> pd.DataFrame:

        curve['J_GEO [A/cm2]'] = curve['Im']/geometrical_area
        curve['E vs RHE [V]'] = curve['Vf'] + reference_potential
        curve['T [s]'] = curve['T']

        if hasattr(self, 'Ru'):
            curve['E_iR vs RHE [V]'] = curve['Vf'] + reference_potential - self.Ru * curve['Im']
            return curve[['E vs RHE [V]', 'E_iR vs RHE [V]', 'J_GEO [A/cm2]']]
        
        curve = curve.reset_index(drop=True)

        return curve[['T [s]', 'E vs RHE [V]', 'J_GEO [A/cm2]']]


    def get_current_at_time(self, time):
        '''Method to get current at specific time. This functionality is mainly for 
        sampled voltammetry, where one wishes to eliminate the non-faradaic currents.
        
        Args:
        self (Chronoamperometry): i-E data, meta_data containing the applied potential
        time (Float or Int): the timestamp at which the current is read. Must be within the time limits
        
        Returns:
        current (float)
        '''

        for curve in self.data_list:
            maximum_time = curve['T'].iloc[-1]
            if time > maximum_time:
                time_input = ask_user(messages.input_messages['time_not_in_range'], (float, int), time_in_seconds = maximum_time)
                return self.get_current_at_time(time_input)

            closest_index = (curve['T'] - time).abs().idxmin()
            current = curve.iloc[closest_index]['J_GEO [A/cm2]']
            self.current = current
            return current
        

    def pick_current(self):

        time, potential, current = self.data_list[0]['T'], self.data_list[0]['E vs RHE [V]'], self.data_list[0]['J_GEO [A/cm2]']
        fig, ax = plt.subplots()
        line, = ax.plot(time, current)
        selected_point, = ax.plot([], [], 'ro')
        plt.xlabel("T [s]")
        plt.ylabel("Current density [A/cm2]")
        ax.legend()

        def onclick(event):
            if event.inaxes != ax:
                return
            x_click = event.xdata
            y_click = event.ydata
            distances = np.sqrt((time - x_click)**2 + (current - y_click)**2)
            idx = np.argmin(distances)
            x_sel = time[idx]
            y_sel = current[idx]
            
            pot_iR = potential[idx] - current[idx]

            selected_point.set_data([x_sel], [y_sel])
            fig.canvas.draw()

            # Save point and close plot
            self.time = x_sel
            self.current = y_sel
            self.potential = pot_iR
            plt.close(fig)

        cid = fig.canvas.mpl_connect('button_press_event', onclick)
        plt.show()
        
    def get_parameter_dict(self):

        results_dict = {'id': self.id, 'current': self.current}
        return results_dict