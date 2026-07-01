from core.experiments.base import Experiment
from os.path import basename

class  Sample():
    """Simple container class for experiment objects.
    
    The Sample object is defined at first by the folder name in loader/manager
    combination, however it can be anything. Iterating over the Sample object
    yields the experiments. 
    """
    
    def __init__(self, sample_name: str, sequence_path = None):
        
        self.sample_path = sample_name
        self.sample_name = basename(sample_name)
        self.gsequence = sequence_path
        self.short_name = self.sample_name[0:15]
        self.experiments:list[Experiment] = []

    def add_experiment(self, experiment:Experiment):
        self.experiments.append(experiment)
        self.experiments.sort(key = lambda x: x.date_time)

    def set_sequence(self, gsequence_path):
        setattr(self, "gsequence", gsequence_path)
        for experiment in self.experiments:
            print('Setting gsequence ', gsequence_path, 'for ', experiment)
            setattr(experiment, "gsequence", gsequence_path)


    def __repr__(self):
        return f"Sample({self.sample_name}, exps={len(self.experiments)})"

    def __iter__(self):
        return iter(self.experiments)
    