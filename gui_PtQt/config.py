from pathlib import Path
import json
import pandas as pd
from experiments.reference_electrode import ReferenceElectrode

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

    def get_electrode(self, label = None, electrode_type = None, all = False, group = False) -> list[ReferenceElectrode] | dict[str:ReferenceElectrode]:
        """Function to retrieve ReferenceElectrode objects based on query. You can search electrdoes
        by label (e.g AM), electrode_type (e.g. AgCl/Ag) or get all of them (all = True) either grouped
        (group = True) or a flat list of all electrodes (group = False)"""
        
        electrodes_to_get = []
        if label:
            for electrode_type_in_dict, electrodes in self.electrodes.items():
                if label in electrodes.keys():
                    electrodes_to_get.append(electrodes[label])
        if electrode_type:
            electrodes_to_get = list(self.electrodes[electrode_type].values())

        if all:
            for electrode_type_in_dict, electrodes in self.electrodes.items():
                if electrodes:

                    # returning e.g. {'AgCl/Ag': [list_of_electrodes]}
                    if group is True:
                        electrodes_to_get = {electrode_key: list(electrodes.values()) for electrode_key, electrodes in self.electrodes.items() if electrodes}
                    
                    # returns a flat list of all electrodes
                    elif group is False:
                        electrodes_to_get = [electrode for electrodes in self.electrodes.values() for electrode in electrodes.values() if electrodes]
                        
        return electrodes_to_get

    def construct_from_json(self):

        for electrode_type, electrodes in self._settings.items():
            category = self.electrodes.setdefault(electrode_type, {})

            for electrode_label, electrode_measurements in electrodes.items():
                if electrode_measurements:
                    electrode = ReferenceElectrode(electrode_type, electrode_label, electrode_measurements)
                    category[electrode_label] = electrode

    def get_electrodes_data(self, electrodes: list[ReferenceElectrode]) -> pd.DataFrame:
        result = map(ReferenceElectrode.get_calibration_data, electrodes)
        return pd.concat(result, axis = 1)
    
    def create_electrode(self, electrode_type, label):
        
        new_electrode =ReferenceElectrode(type = electrode_type, label = label, dictionary = None)
        self.electrodes[electrode_type].setdefault(label, new_electrode)
        return new_electrode

# Tworzysz gotowe instancje raz, w jednym miejscu
settings = JsonManager("settings.json")
references = ReferenceManager()
icon_path = 'Fugue_icons/fugue-icons-3.5.6/icons/'