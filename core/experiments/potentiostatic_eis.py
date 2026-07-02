from .base import *

class EIS(Experiment):
    def __init__(self, file_path, date_time, id, tag, cycle):
        super().__init__(file_path, date_time, id, tag, cycle)

    def process_data(self):
        
        result = super().process_data()
        return result

    def get_multiindex_labels(self, columns, curve_index, add_curve_index = True) -> tuple[list[list[str]], list[str]]:
        """
        Returns levels and names for multiindexing. Is different for each 
        type of experiment.
        Returns:
        - list of lists: values for each level of the Multiindex (e.g. [[path], [curve_name], [column1, column2, column2, ...]])
        - list of level names (e.g. ['Path, 'Curve', 'Metric])
        """
        final_potential = self.meta_data['VDC'] + self.reference_potential
        final_potential = '{:.3f}'.format(final_potential)

        level_values = [[self.file_path], [final_potential], columns]
        level_names = ['Path', 'E vs RHE [V]', 'Parameter']
        return level_values, level_names

    def _add_computed_column(self, curve:pd.DataFrame) -> pd.DataFrame:
        
        curve = curve.reset_index(drop=True)
        curve = curve[['Freq','Zreal','Zimag']]
        curve['Zimag'] = -curve['Zimag']
        curve.columns = ['Freq [Hz]', 'Zreal [Ohm]', '-Zimag [Ohm]']
        return curve
    
    def get_Ru(self):
        """
        Quick function to grab the high frequency real impedance part 
        which is most of the time realted to uncompenasted resistance (Ru).
        
        Args:
            self (EIS): EIS object.
        
        Returns:
            Ru_val (float): Uncompenasted resistance taken from the first quarter 
            of measurement points (to not get values from low frequency range)."""

        if not self.isProcessed:
            self.process_data()
        
        z_real, z_imag = self.get_xy_data(0)
        
        # first ten values to include only high-frequency measurement points
        number_of_points = len(z_imag)
        high_frequency_number_of_points = int(round(number_of_points/4, 0 ))
        imag_value = z_imag[0:high_frequency_number_of_points].idxmin()
        Ru_val = z_real[imag_value]
        return Ru_val
            
    
    @property
    def default_x(self) -> str:
        """Dla EIS osią X jest zawsze Z'."""
        return 'Zreal [Ohm]'

    @property
    def default_y(self) -> str:
        """Dla EIS osią Y jest zawsze -Z"."""
        return '-Zimag [Ohm]'

    @property
    def default_x_plot(self) -> str:
        """Dla EIS osią X jest zawsze Z'."""
        return 'Z\' [Ω]'

    @property
    def default_y_plot(self) -> str:
        """Dla EIS osią Y jest zawsze -Z"."""
        return '-Z" [Ω]'