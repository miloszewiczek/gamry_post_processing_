from pathlib import Path
import json
import os
import pandas as pd
from operator import itemgetter

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
        
    def get_electrode_names(self, electrode_type) -> list[str]:
        if electrode_type == '<all>':
            test = [obj for x in self._settings.values() for obj in x.keys()]
            print(test)
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
        return pd.concat(tmp, axis = 1)

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
        
# Tworzysz gotowe instancje raz, w jednym miejscu
settings = JsonManager("settings.json")
references = ReferenceManager()