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

        self.construct_from_json()
    
    def get_all_data(self):
        df = pd.DataFrame(self._settings)
        df.index = pd.to_datetime(df.index)
        return df

    def get_electrode_types(self):
        return self._settings.keys()

    def get_electrodes(self, electrode_type) -> dict:
        
        try:
            return self._settings[electrode_type]
        except:
            return
        
    def get_electrode_names(self, electrode_type = '<all>') -> list[str]:
        if electrode_type == '<all>':
            test = [obj for x in self._settings.values() for obj in x.keys()]
            return test

        try:
            return list(self._settings[electrode_type].keys())
        except:
            return

    def get_all_electrode_data(self) -> pd.DataFrame:
        tmp = []
        for electrode_type in self._settings.keys():
            df = self.get_electrode_data(electrode_type)
            tmp.append(df)

        try:
            return pd.concat(tmp, axis = 1)
        except:
            return None

    def get_electrode_info(self, electrode):
        for electrode_type in self._settings.values():
            if electrode in electrode_type.keys():
                return electrode_type.get(electrode)
        return
    

    def get_newest_calibration(self, electrode_dict):
        if isinstance(electrode_dict, dict):
            dates = list(electrode_dict.keys())
            date_format = "%Y-%m-%d %H:%M:%S"
            sorted_dates = sorted(dates, key = lambda x: datetime.strptime(x, date_format))
            freshest_calibration = sorted_dates[-1]
            days_since_last_calibration = datetime.now() - datetime.strptime(freshest_calibration, date_format)
            days = days_since_last_calibration.days
            
            return electrode_dict[freshest_calibration], days
        else:
            return


    def get_electrode_data(self, electrode_type) -> pd.DataFrame:
        
        tmp = []
        electrode_dict = self.get_electrodes(electrode_type)
        if electrode_dict:
            for label, ito in electrode_dict.items():

                df = pd.DataFrame.from_dict(ito, orient = 'index')[['calibration offset [V]']]
                df.columns = [label,]
                tmp.append(df)

            df_new = pd.concat(tmp, axis = 1)
            print(df_new)
            return df_new

        print('no')
        return

        
    def add_measurement(self, electrode_id, electrode_type, date, file_path, time, offset,  notes = None):
        to_add = {
                "filepath": file_path,
                "time at offset [s]": time,
                "calibration offset [V]": offset,
                "notes": notes
            }


        electrode = self._settings[electrode_type].setdefault(electrode_id, {})

        # 3. Dodajemy lub aktualizujemy pomiar dla konkretnej daty
        electrode[date] = to_add

    def construct_from_json(self):
        self.electrodes = {}
        for electrode_type, electrodes in self._settings.items():
            for electrode_label, electrode_measurements in electrodes.items():
                if electrode_measurements:
                    electrode = ReferenceElectrode(electrode_type, electrode_label, electrode_measurements)
                    x = self.electrodes.setdefault(electrode_type, {electrode_label: electrode})
                    print(x)
        

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