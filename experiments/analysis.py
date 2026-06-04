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
    
    def __repr__(self):
        return f'Analysis name: {self.name}\nList of experiments: {self.experiments}\n'


# Definiujemy unikalny typ dla poziomów Twojego MultiIndexu
IndexLevel = Literal['Sample', 'Cycle', 'Experiment']

class OverpotentialAnalysis(BaseAnalysis):
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
    

def create_multiindex_analysis(index_names: list[str], data):
