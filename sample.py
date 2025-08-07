from experiments import *
from core import ExperimentLoader, ExperimentManager
from functions.functions import calculate_ECSA_from_slope
import json
from slider import InteractivePlotApp

loader = ExperimentLoader()
manager = ExperimentManager()

#EXAMPLE WORKFLOW
#loader.load_testing()

loader.choose_folder()
manager.list_of_experiments = loader.list_of_experiments
manager.filter(object_type=ECSA)
x = manager.filtered[0]
x.load_data()
x.process_data()

app = InteractivePlotApp(x)
app.mainloop()

def load_config():
    with open('app_config/settings2.json', 'r') as f:
        data = json.load(f)
    return data
#x = load_config()
