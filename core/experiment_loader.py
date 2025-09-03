from experiments import *
import os
from datetime import datetime
import re
from itertools import chain
from tkinter.filedialog import askopenfilenames

class ExperimentLoader():
    '''An interface class to aggregate and manage the experiments. '''

    def __init__(self):
        '''All of the experiments are stored in the variable self.experiments'''
        self.experiments = {}
        self.filtered = {}
        self.list_of_experiments = []
        self.id_counter = 0
        
        #Default settings, always implemented in the program
        self.experiment_classes = {
            'IDENTIFIERS':{
                "MYCIE" : Voltammetry,
                #"CHRONOA" : Chronoamperometry,
                #"EIS" : EIS,
                "HER" : LinearVoltammetry,
                "ECSA" : ECSA,
                "Open Circuit Potential": OpenCircuit
                },
            'TAGS':{
                "CV" : Voltammetry,
                "LSV" : LinearVoltammetry,
                "CORPOT" : OpenCircuit,
                "CHRONOA" : Chronoamperometry,
                "EISPOT": EIS
                }
        }
    
    def update_counter(self, delta):
        self.id_counter += delta
        return self.id_counter

    def load_testing(self):
        """Helper function for testing of the program. 
        Loads all the files in the input folder."""
        
        files = [os.path.join('input/', file) for file in os.listdir('input/') if os.path.isfile(os.path.join('input/', file))]
        for file in files:
            self.create_experiment(file)
        print('Added testing files (input/*)')
        return self.list_of_experiments

    def choose_files(self):
        """
        A function to choose files from a folder based on tkinter askopenfilenames.
        
        Args:
            self (ExperimentLoader)
        
        Returns:
            list_of_experiments (list) - a list of Experiment objects. The list is also set as the attribute of the same name for the loader"""
        files = askopenfilenames(filetypes=[('Gamry Experiment Files', '*.DTA')])

        list_of_experiments = []
        for file in files:
            experiment = self.create_experiment(file)
            if experiment is not None:
                list_of_experiments.append(experiment)
                self.update_counter(+1)
        return list_of_experiments
        
    def create_experiment(self, file_path):
        '''Factory function to create the experiment and store it in a manager.
        Depending on the TAG of the .DTA file, it creates a different experiment object characterized by different data processing methods.'''

        with open(file_path, 'r') as tmp_experiment:
            lines = tmp_experiment.readlines()

            if len(lines) == 0:
                return

            for line in lines:
                if 'TAG' in line:
                    experiment_tag = line.split()[1]
                if 'TITLE' in line:
                    match = re.search(r'LABEL\s+(.*?)\s+Test Identifier', line)
                    experiment_identifier = match.group(1)
                if 'DATE' in line:
                    experiment_date = line.split()[2]
                if 'TIME' in line:
                    experiment_time = line.split()[2]
                    try:
                        date_time = datetime.strptime(experiment_date + ' ' + experiment_time, '%d.%m.%Y  %H:%M:%S')
                    except ValueError:
                        date_time = datetime.strptime(experiment_date + ' ' + experiment_time, '%m/%d/%Y  %H:%M:%S')
                    break

        experiment_id = self.id_counter

        #RETURNS DIFFERENT CLASS DEPDENDING ON THE IDENTIFIER AND TAG
        experiment_class = self.get_experiment_class(experiment_identifier = experiment_identifier,
                                                     experiment_tag = experiment_tag)
        
        #OLD FUNCTION, RETURNS CYCLE NUMBER
        experiment_keys = self.parse_filename(file_path)

        
        #CREATION OF EXPERIMENT INSTNANCE
        experiment = experiment_class(file_path = file_path,
                        date_time = date_time,
                        id = experiment_id,
                        tag = experiment_identifier,
                        cycle = experiment_keys[1])
        
        #self.add_experiment(experiment)
        
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