from .base import *

class LinearVoltammetry(Experiment):
    def __init__(self, file_path, date_time, id, tag, cycle):
        super().__init__(file_path, date_time, id, tag, cycle)
        self.tafel_curves = []
        self.tafel_analysis = []
    
    def process_data(self) -> pd.DataFrame:
        
        result = super().process_data()

        return result

    def _add_computed_column(self, curve):
        LSV_curve =  super()._add_computed_column(curve)
        curve['log10 J_GEO [A/cm2]'] = np.log10(0-LSV_curve['J_GEO [A/cm2]'])
        Tafel_curve = pd.concat([curve['log10 J_GEO [A/cm2]'], LSV_curve['E vs RHE [V]']], axis=1)
        self.tafel_curves.append(Tafel_curve)

        return pd.concat([LSV_curve, Tafel_curve], axis=1)

    def get_multiindex_labels(self, columns, curve_index, add_curve_index=True):

        level_values = [[f'{self.file_path}'], columns]
        level_names = ['Path', 'Parameter']
        return level_values, level_names
    
    def calculate_overpotentials(self, curves:list[pd.DataFrame] = None, ECSA = None, GEO = -10):

        tmp = defaultdict(list)
        if not isinstance(GEO, list):
            GEO = [GEO]
        
        if curves is None:
            if not getattr(self, 'processed_data'):
                print(messages.error_messages['reqeuest_processing'])
                return
            curves = self.processed_data

        for curve in curves:
            for current in GEO:
                if current < 0: 
                    mask = curve['J_GEO [A/cm2]'] * 1000 < current
                elif current > 0:
                    mask = curve['J_GEO [A/cm2]'] * 1000  > current
                
                index = mask.idxmax()
                overpotential = curve.at[index, 'E vs RHE [V]'].iloc[0] #ADDING ILOC BECAUSE FOR SOME REASON THE at FUNCTION RETURNED AN ARRAY WITH LEN = 2
                tmp[current].append(overpotential)
                
        self.overpotential_data = tmp

        return tmp

    def calculate_tafel_slope(self, starting_point, step, overlap, data = None, name = 'Sample', curve_number = None, i = None):
        '''
        Function to calcualte the tafel slope based on a publication entitled: 
        Tafel Slope Plot as a Tool to Analyze Electrocatalytic Reactions
        DOI: 10.1021/acsenergylett.4c00266

        It takes I-E data, and calculates the Tafel slope over a small current region, which is then
        averaged. The step continues recursively until the potential is out of bounds of the experiment.
        The data can then be plotted as TafelSlope = f(Avereage log10 Current) to observe regions with 
        nearly constant Tafel slopes. The average of that regeion is the true Tafel slope.

        Args:
        self: LinearVoltammetry (the functionality can be extended to non-transient techniques such as chronoamperometric measurements)
        data: I-E data, here taken from the tafel_curves attribute.
        starting_point: the potential at which the calculations start, most of the time 0 V vs RHE (in V!)
        step: potential step used in successive calculations. Remember about the sign! Need to be chosen experimentally (in V!)
        overlap: the same data can be used in successive calculations (in V!)
        
        Returns:
        self.tafel_analysis: pd.DataFrame
        '''
        if data is None:
            data = self.tafel_curves[0]

        i_start = (np.abs(data['E vs RHE [V]'] - starting_point)).argmin()
        print(messages.processing_messages['tafel_slope_new'][0].format(i_start = i_start))
        search = data['E vs RHE [V]'][i_start]
        print(messages.processing_messages['tafel_slope_new'][1].format(potential = search))
        new_search = search + step
        print(messages.processing_messages['tafel_slope_new'][2].format(new_potential = new_search))
        idx = (np.abs(data['E vs RHE [V]'] - new_search)).argmin()
        print(messages.processing_messages['tafel_slope_new'][3].format(i_end = idx))

        new_search_overlap = new_search - overlap
        print(messages.processing_messages['tafel_slope_new'][4].format(overlap = overlap, new_potential_with_overlap = new_search_overlap))

        x = data['log10 J_GEO [A/cm2]'][i_start:idx]
        y = data['E vs RHE [V]'][i_start:idx]

        try:
            slope, intercept = np.polyfit(x, -y, 1)
            average_current = np.mean(x)
            self.tafel_analysis.append([search, new_search, average_current, slope])
            cont_calculation = True
        except:
            print(messages.processing_messages['tafel_slope_new'][5])
            cont_calculation = False

        if min(data['E vs RHE [V]']) < new_search and cont_calculation:
            
            self.calculate_tafel_slope(new_search_overlap, step, overlap = overlap, data = data, name = name, curve_number = curve_number, i = 1)

        else:
            try:
                self.tafel_analysis = pd.DataFrame(self.tafel_analysis, columns = ['E1 [V]', 'E2[V]', 'Average log10 J_GEO [A/cm2]', 'Tafel Slope [V/dec]'])
                return self.tafel_analysis
            except:
                return 'Couldnt do that, dummy'

    def visualize_tafel(self):

        fig, ax = plt.subplots(figsize=(15,10))
        plt.xlabel('Average log10 j [mA/cm2]')
        plt.ylabel('Tafel slope [mV/dec]')
        plt.title(self.file_path)
        
        print('Calculated finish index is lower than starting index. Aborting. This is due to iR-drop and bubbles detachment.')
        #df = pd.DataFrame(output[curve_number], columns = ['E_begining', 'E_final', 'Average current [mA/cm2]', 'Tafel slope [mV/dec]'])
        #resulting_dfs.append(df)

        x_data = self.tafel_analysis['Average log10 J_GEO [A/cm2]']
        y_data = self.tafel_analysis['Tafel Slope [V/dec]']
        ax.scatter(x_data,y_data)
        #ax.set_ylim(0,150)
        clicked_points = []
        selected = None

    
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

        return selected


    def get_parameter_dict(self):

        return self.overpotential_data
    
    def perform_postprocessing(self, **kwargs):
        
        return self.calculate_overpotentials(**kwargs)