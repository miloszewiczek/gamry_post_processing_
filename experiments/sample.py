from experiments.base import Experiment

class   Sample():
    def __init__(self, sample_name: str):
        self.sample_name = sample_name
        self.experiments:list[Experiment] = []

    def add_experiment(self, experiment:Experiment):
        self.experiments.append(experiment)
        self.experiments.sort(key = lambda x: x.date_time)
    
    def clone(self, new_id, exp_loader):
        new_sample = Sample(sample_name = self.sample_name + "_Copy")
        for exp in self.experiments:
            new_exp 

    def __repr__(self):
        return f"Sample({self.sample_name}, exps={len(self.experiments)})"

    def __iter__(self):
        return iter(self.experiments)