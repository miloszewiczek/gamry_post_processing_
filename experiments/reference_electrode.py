from datetime import datetime
from pandas import DataFrame

class ReferenceElectrode():
    def __init__(self, type, label, dictionary = None):
        self.type = type
        self.label = label
        self.measurements = {}
        self.date_format = "%Y-%m-%d %H:%M:%S"

        if dictionary:
            self.add_dictionary(dictionary)
            self.sort()
        
    def add_data(self, date_time, file_path, time_at_offset, calibration_offset, notes):
        dict_to_save = {
            'filepath': file_path,
            'time at offset [s]': time_at_offset,
            'calibration offset [V]': calibration_offset,
            'notes': notes
        }
        
        date_time = datetime.strptime(date_time, self.date_format)
        self.measurements[date_time] = dict_to_save 
    
    def add_dictionary(self, measurement_dict):

        for date_time, measurement_info in measurement_dict.items():
            date_time = datetime.strptime(date_time, self.date_format)
            self.measurements[date_time] = measurement_info
    
    def sort(self):
        print('sorting...')
        sorted_dates = sorted(self.measurements.keys())
        self.measurements = {k: self.measurements[k] for k in sorted_dates}
        self.last_calibration_date = sorted_dates[-1]
        self.last_calibration_data = self.measurements[self.last_calibration_date] 
        self.isSorted = True
        
    def calculate_last_calibration(self):
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

    def get_calibration_data(self):
        if self.measurements:
            df = DataFrame.from_dict(self.measurements, orient = 'index')[['calibration offset [V]']]
            df.columns = [self.label,]
            return df
        return
    
    def get_calibration_offset(self):
        if self.last_calibration_data:
            return self.last_calibration_data['calibration offset [V]']
        return
    
    def get_dict(self):
        return {str(date_time): measurement for date_time, measurement in self.measurements.items()}