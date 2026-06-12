from datetime import datetime
from pandas import DataFrame

class ReferenceElectrode():
    """
    Class related to reference electrodes in electrochemistry. 

    The main idea is that the potential of these electrodes is a 
    function of time. To compensate for that, they are calibrated via 
    open circuit potential measurements (OCP) versus a reference electrode
    of a known potential the so called Mother Electrode.

    After each calibration, the data is saved to:
    gui_PtQt/reference_potentials.json file

    Currently the following electrode types are implemented:
    - AgCl/Ag (3M KCl)
    - Hg2Cl2/Hg (3M KCl)
    - HgO/Hg (3M KOH)
    """

    def __init__(self, type, label, dictionary = None):
        self.type = type # currently, the type is one of the following
        self.label = label
        self.measurements = {}
        self.date_format = "%Y-%m-%d %H:%M:%S"

        if dictionary:
            self.add_dictionary(dictionary)
            self.sort()
        
    def add_data(self, date_time, file_path, time_at_offset, calibration_offset, notes):
        """
        Adding data to a ReferenceElectrode object.
        
        Args:
            date_time (datetime): A timestamp for the data added.
            file_path (str): File path of the OCP experiment used to get the data from.
            time_at_offset (float): Time at which the potential was from OCP was read.
            calibration_offset (float): OCP potential at time defined by time_at_offset.
            notes (str): Info provided by the user about the data.
            
        Returns:
            dict_to_save (dict): Dictionary entry created from the function based on input parameters."""
        
        dict_to_save = {
            'filepath': file_path,
            'time at offset [s]': time_at_offset,
            'calibration offset [V]': calibration_offset,
            'notes': notes
        }
        
        date_time = datetime.strptime(date_time, self.date_format)
        self.measurements[date_time] = dict_to_save 
        return dict_to_save
    
    def add_dictionary(self, measurement_dict):

        for date_time, measurement_info in measurement_dict.items():
            date_time = datetime.strptime(date_time, self.date_format)
            self.measurements[date_time] = measurement_info
    
    def sort(self):
        """
        Quick sort based on dates of the OCP experiments.
        """
        sorted_dates = sorted(self.measurements.keys())
        self.measurements = {k: self.measurements[k] for k in sorted_dates}
        self.last_calibration_date = sorted_dates[-1]
        self.last_calibration_data = self.measurements[self.last_calibration_date] 
        self.isSorted = True
        
    def calculate_last_calibration(self):
        """
        Calculate days since last calibration.
        """

        difference = datetime.now() - self.last_calibration_date
        days = difference.days
        return days
 
    def get_info(self) -> dict:
        if self.measurements:
            self.sort()
            days = self.calculate_last_calibration()
            self.last_calibration_data['last_calibration_date'] = days
            return self.last_calibration_data
        return

    def get_calibration_data(self) -> DataFrame:
        """
        Function that returns a dataframe of calibration offset vs time.
        """

        if self.measurements:
            df = DataFrame.from_dict(self.measurements, orient = 'index')[['calibration offset [V]']]
            df.columns = [self.label,]
            return df
        
        return
    
    def get_calibration_offset(self, date_time:str = None) -> float:
        """
        Function that returns the calibration offset at a specific date time.
        
        Args:
            date_time (str): date time string at which to get the calibration offset.

        Returns:
            calibration_offset (float): Calibration offset at specific date_time."""
        if self.measurements:
            if date_time == None:
                calibration_offset = self.last_calibration_data.get('calibration offset [V]')
            else:
                calibration_offset = self.measurements[date_time].get('calibration offset [V]')
            return calibration_offset
        return
    
    def get_dict(self):
        return {str(date_time): measurement for date_time, measurement in self.measurements.items()}