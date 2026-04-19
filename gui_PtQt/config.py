class SettingsManager:
    _instance = None
    _settings = {}
    FILE_PATH = "settings.json"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SettingsManager, cls).__new__(cls)
            cls._instance._load_from_file()
        else:
            return