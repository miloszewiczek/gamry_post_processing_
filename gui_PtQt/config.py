from pathlib import Path
import json
import os
import pandas as pd
from datetime import datetime, date

class JsonManager:
    def __init__(self, filename):
        self.file_path = Path(__file__).resolve().parent / filename
        self._settings = {}
        self.load()

    def load(self):
        if self.file_path.exists():
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self._settings = json.load(f)
        else:
            self._settings = {"area": 1}

    def get(self, key, default=None):
        return self._settings.get(key, default)

    def set(self, key, value):
        self._settings[key] = value
        self.save()

    def save(self):
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self._settings, f, indent=4)

db = {}
class ReferenceManager(JsonManager):
    def __init__(self):
        super().__init__("reference_potentials.json")


        self.electrodes = {}
        self.construct_from_json()

    def get_electrode(self, label = None, electrode_type = None, all = False):
        
        electrodes_to_get = []
        if label:
            for electrode_type_in_dict, electrodes in self.electrodes.items():
                if label in electrodes.keys():
                    electrodes_to_get.append(electrodes[label])
        if electrode_type:
            electrodes_to_get = list(self.electrodes[electrode_type])

        if all:
            for electrode_type_in_dict, electrodes in self.electrodes.items():
                if electrodes:
                    electrodes_to_get = {electrode_key: list(electrodes.values()) for electrode_key, electrodes in self.electrodes.items() if electrodes}
        return electrodes_to_get

    def construct_from_json(self):

        for electrode_type, electrodes in self._settings.items():
            category = self.electrodes.setdefault(electrode_type, {})

            for electrode_label, electrode_measurements in electrodes.items():
                if electrode_measurements:
                    electrode = ReferenceElectrode(electrode_type, electrode_label, electrode_measurements)
                    category[electrode_label] = electrode

class ReferenceElectrode():
    def __init__(self, type, label, dictionary = None):
        self.type = type
        self.label = label
        self.measurements = {}
        self.date_format = "%Y-%m-%d %H:%M:%S"

        if dictionary:
            self.add_dictionary(dictionary)
        
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

        sorted_dates = sorted(self.measurements.keys())
        self.measurements = {k: self.measurements[k] for k in sorted_dates}
        self.last_calibration_date = sorted_dates[-1]
        self.last_callibration_data = self.measurements[self.last_calibration_date] 
        self.isSorted = True
        
    def calculate_last_calibration(self):
        difference = datetime.now() - self.last_calibration_date
        days = difference.days

        return days
 
    def get_calibration_data(self):
        df = pd.DataFrame.from_dict(self.measurements, orient = 'index')[['calibration offset [V]']]
        df.columns = [self.label,]
        return df

# Tworzysz gotowe instancje raz, w jednym miejscu
settings = JsonManager("settings.json")
references = ReferenceManager()