from core.experiments import *
import os
from datetime import datetime
import re
from itertools import chain
from glob import glob
from tkinter.filedialog import askopenfilenames, askdirectory
from random import sample

class ExperimentLoader():
    def __init__(self):
        self.experiments = {}
        self.filtered = {}
        self.list_of_experiments = []
        self.id_counter = 0
        
        self.experiment_classes = {
            'IDENTIFIERS': {
                "MYCIE": Voltammetry,
                "CHRONOA": Chronoamperometry,
                "EIS": EIS,                      # Odkomentowane
                "HER": LinearVoltammetry,
                "ECSA": ECSA,
                "Open Circuit Potential": OpenCircuit
            },
            'TAGS': {
                "CV": Voltammetry,
                "LSV": LinearVoltammetry,
                "CORPOT": OpenCircuit,
                "CHRONOA": Chronoamperometry,
                "EISPOT": EIS,
                "EISGALV": EIS,                  # Dodany wariant galwanostatyczny
                "EIS": EIS                       # Dodany ogólny tag EIS
            }
        }
    
    def update_counter(self, delta):
        self.id_counter += delta
        return self.id_counter

    def load_testing(self,  sample_size):

        current_dir = os.path.dirname(os.path.abspath(__file__))
        input_path = os.path.join(current_dir, '../..', 'input')
        input_path = os.path.normpath(input_path)

        if not os.path.exists(input_path):
            print(f"BŁĄD: Folder nie istnieje pod ścieżką: {input_path}")
            return self.list_of_experiments

        files = [os.path.join(input_path, f) for f in os.listdir(input_path) 
                if os.path.isfile(os.path.join(input_path, f))]
        
        random_files = sample(files, sample_size)
        list_of_experiments = [self.create_experiment(file) for file in random_files]

        dict_of_experiments = {}
        for experiment in list_of_experiments:
            if experiment is not None:
                dict_of_experiments[getattr(experiment, 'id')] = experiment
        return dict_of_experiments
    
    def load(self, path:str):
        from pathlib import Path
        path_to_files = Path(path).glob('*.DTA')
        list_of_experiments = [self.create_experiment(str(file)) for file in path_to_files]
        dict_of_experiments = {}
        for experiment in list_of_experiments:
            if experiment is not None:
                dict_of_experiments[getattr(experiment, 'id')] = experiment
        return dict_of_experiments

    def populate_list_of_experiments(self,files):

        dict_of_experiments = {}
        for file in files:
            experiment = self.create_experiment(file)
            if experiment is not None:
                dict_of_experiments[getattr(experiment, 'id')] = experiment
        return dict_of_experiments

    def get_counter(self):
        return self.id_counter

    def choose_files(self):
        """
        A function to choose files from a folder based on tkinter askopenfilenames.
        
        Args:
            self (ExperimentLoader)
        
        Returns:
            list_of_experiments (list) - a list of Experiment objects. The list is also set as the attribute of the same name for the loader"""
        files = askopenfilenames(filetypes=[('Gamry Experiment Files', '*.DTA')])
        return self.populate_list_of_experiments(files)
    
    def choose_folder(self):
        """
        A function to choose files from a folder based on tkinter askopenfilenames.
        
        Args:
            self (ExperimentLoader)
        
        Returns:
            list_of_experiments (list) - a list of Experiment objects. The list is also set as the attribute of the same name for the loader"""
        
        from core.functions.gui_functions import load_folder 
        files = load_folder

        return self.populate_list_of_experiments(files)

        
    def create_experiment(self, file_path, manager=None) -> Experiment:
        '''Factory function to create the experiment and store it in a manager.'''

        # 1. Bezpieczne kodowanie Windows-1252 z ignorowaniem błędów znaków specjalnych (°C, omy itp.)
        try:
            with open(file_path, 'r', encoding='cp1252', errors='replace') as tmp_experiment:
                lines = tmp_experiment.readlines()
        except:
            with open(file_path, 'r', encoding = 'iso-8859-1') as tmp_experiment:
                print('Pringiting lines now:')
                lines = tmp_experiment.readlines()
        if len(lines) == 0:
            return None

        experiment_tag = None
        experiment_identifier = None
        date_time = None
        experiment_date = None
        experiment_time = None

        # 2. Bezpieczne parsowanie nagłówka (przeszukujemy pierwsze 60 linii zamiast przerywać za wcześnie)
        for line in lines[:80]:
            if 'TAG' in line and not experiment_tag:
                parts = line.split()
                if len(parts) > 1:
                    experiment_tag = parts[1]

            if 'TITLE' in line and not experiment_identifier:
                match = re.search(r'LABEL\s+(.*?)\s+Test &?Identifier', line)
                if match:
                    experiment_identifier = match.group(1).strip()

            if 'DATE' in line and not experiment_date:
                parts = line.split()
                if len(parts) > 2:
                    experiment_date = parts[2]

            if 'TIME' in line and not experiment_time:
                parts = line.split()
                if len(parts) > 2:
                    experiment_time = parts[2]

            # Kończymy szukanie dopiero, gdy znajdziemy wszystkie kluczowe parametry
            if experiment_tag and experiment_identifier and experiment_date and experiment_time:
                break

        # Parsowanie daty
        if experiment_date and experiment_time:
            for fmt in ('%d.%m.%Y %H:%M:%S', '%m/%d/%Y %H:%M:%S', '%d/%m/%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S'):
                try:
                    date_time = datetime.strptime(f"{experiment_date} {experiment_time}", fmt)
                    break
                except ValueError:
                    pass
        
        if date_time is None:
            date_time = datetime.now()

        experiment_id = self.id_counter
        self.update_counter(+1)

        experiment_class = self.get_experiment_class(
            experiment_identifier=experiment_identifier,
            experiment_tag=experiment_tag
        )
        
        experiment_keys = self.parse_filename(file_path)

        experiment = experiment_class(
            file_path=file_path,
            date_time=date_time,
            id=experiment_id,
            tag=experiment_identifier if experiment_identifier else (experiment_tag or "UNKNOWN"),
            cycle=experiment_keys[1] if experiment_keys else None
        )

        if manager is not None:
            manager.update(experiment)

        return experiment
                    
    def get_experiment_class(self, experiment_identifier, experiment_tag):
        """Helper function to retrieve and in other case 
        add a new Experiment subclass to class fac"""

        experiment_class = self.experiment_classes['IDENTIFIERS'].get(experiment_identifier)

        if not experiment_class:
            experiment_class = self.experiment_classes['TAGS'].get(experiment_tag)
            if not experiment_class:
                self.experiment_classes['IDENTIFIERS'][experiment_identifier] = Experiment
                experiment_class = self.experiment_classes['IDENTIFIERS'].get(experiment_identifier)

        return experiment_class
    
    def parse_filename(self, filename:str) -> tuple[str, int]:
        """Helper function to parse the file given by filename and 
        returns a tuple containing experiment_name, cycle"""

        match = re.match(r"(.+?)_#(\d+)(?:_#\d+)?\.DTA$", filename)
        if match:
            experiment_name = match.group(1)
            experiment_name = os.path.basename(experiment_name)
            cycle = int(match.group(2)) if match.group(2) else None


            return (experiment_name, cycle)
        match = re.match(r"(.+?).DTA$", filename)
        if match:

            experiment_name = match.group(1)
            experiment_name = os.path.basename(experiment_name)
            return (experiment_name, None)
        
    def add_experiment(self, experiment):
        """
        Simple function to add an experiment based on a key obtained from parse_filename function
        - `experiment_keys`: a tuple of name, cycle and object type
        - `experiment`: the object of class Experiment or its subclass
        """
        self.list_of_experiments.append(experiment)
