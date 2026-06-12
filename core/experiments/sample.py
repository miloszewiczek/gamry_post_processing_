from core.experiments.base import Experiment
from os.path import basename

class  Sample():
    """Simple container class for experiment objects.
    
    The Sample object is defined at first by the folder name in loader/manager
    combination, however it can be anything. Iterating over the Sample object
    yields the experiments. 
    """
    
    def __init__(self, sample_name: str):
        
        self.sample_path = sample_name
        self.sample_name = basename(sample_name)
        self.short_name = self.sample_name[0:15]
        self.experiments:list[Experiment] = []

    def add_experiment(self, experiment:Experiment):
        self.experiments.append(experiment)
        self.experiments.sort(key = lambda x: x.date_time)

    def __repr__(self):
        return f"Sample({self.sample_name}, exps={len(self.experiments)})"

    def __iter__(self):
        return iter(self.experiments)