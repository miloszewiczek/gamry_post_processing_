import pandas as pd
import numpy as np
from typing import List, Literal, Union, Dict, Any
import pandas as pd

class BaseAnalysis():
    def __init__(self, name, experiments, data, **kwargs):
        
        self.name = name
        self.experiments = experiments
        self.data = data
        for karg in kwargs:
            setattr(self, karg, kwargs[karg])

    def get_dictionary(self):
        return {'Name': self.name,
                'Experiments': self.experiments,
                'Data': self.data}
    
    def __repr__(self):
        return f'Analysis name: {self.name}\nList of experiments: {self.experiments}\n'


# Definiujemy unikalny typ dla poziomów Twojego MultiIndexu


class OverpotentialAnalysis(BaseAnalysis):
    IndexLevel = Literal['Sample', 'Cycle', 'Experiment']
    def __init__(self, name: str, experiments: list, data: pd.DataFrame, **kwargs):
        super().__init__(name, experiments, data, **kwargs)

    def group_by(self, level: Union[IndexLevel, List[IndexLevel]]) -> pd.DataFrame:
        """
        Grupuje dane analizy po wskazanych poziomach indeksu i wylicza mean oraz std.
        
        :param level: Poziom lub lista poziomów do grupowania: 'Sample', 'Cycle', 'Experiment'
        :return: Skonsolidowany DataFrame z MultiIndexem kolumnowym (mean, std)
        """
        # Używamy self.data (zakładam, że tak nazywa się zmienna w klasie bazowej)
        grouped = self.data.groupby(level=level)
        summary_stats = grouped.agg(['mean', 'std'])
        return summary_stats
    
class DoubleLayerAnalysis(BaseAnalysis):
    def __init__(self, name: str, cycle:int, experiments: list, fitting_data: pd.DataFrame, raw_data: pd.DataFrame, potential:float, **kwargs):
        # Przekazujemy fitting_data jako główny "data" do bazy, albo odwrotnie - zależnie od preferencji.
        # Umówmy się, że głównym 'data' będą punkty surowe, a fitting_data przypiszemy jawnie.
        super().__init__(name, experiments, data=raw_data, **kwargs)
        
        self.fitting_data = fitting_data
        self.cycle = cycle
        # Dzięki kwargs, jeśli podasz `potential=chosen_potential`, 
        # automatycznie w klasie bazowej zrobi się self.potential = chosen_potential
