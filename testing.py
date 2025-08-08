from experiments import *
from core import ExperimentLoader, ExperimentManager














if __name__ == '__main__':
    loader = ExperimentLoader()
    manager = ExperimentManager()
    manager.set_experiments(loader.load_testing())
    manager.filter(object_type= LinearVoltammetry)
    
    data = []
    for exp in manager.get_experiments('filtered'):
        
        exp.load_data()
        exp.process_data()
        exp.calculate_tafel_slope(0, -0.025, 0)
        data.append(exp.tafel_analysis)
        exp.visualize_tafel()
    