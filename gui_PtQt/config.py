import os
import json
from pathlib import Path

class SettingsManager:
    _instance = None
    _settings = {}
    BASE_DIR = Path(__file__).resolve().parent
    FILE_PATH = BASE_DIR / "settings.json"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SettingsManager, cls).__new__(cls)
            cls._instance._load_from_file()
        else:
            return  cls._instance
        
    def _load_from_file(self):
        if os.path.exists(self.FILE_PATH):
            with open(self.FILE_PATH, 'r', encoding = 'utf-8') as file:
                self._settings = json.load(file)
        else:
            self._settings = {"area": 1}
    
    def get(self, key, default = None):
        return self._settings.get(key, default)
    
    def set(self, key, value):
        self._settings[key] = value
        self.save()

    def save(self):
        with open(self.FILE_PATH, 'w', encoding = 'utf-8') as file:
            json.dump(self._settings, file, indent = 4)