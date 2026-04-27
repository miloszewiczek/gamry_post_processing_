from pathlib import Path
import json
import os
import pandas as pd

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

class ReferenceManager(JsonManager):
    def __init__(self):
        super().__init__("reference_potentials.json")
    
    def get_all_data(self):
        df = pd.DataFrame(self._settings)
        df.index = pd.to_datetime(df.index)
        return df


# Tworzysz gotowe instancje raz, w jednym miejscu
settings = JsonManager("settings.json")
references = ReferenceManager()