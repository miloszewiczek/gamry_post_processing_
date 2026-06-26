import pandas as pd
import numpy as np
from typing import List, Literal, Union, Dict, Any
import pandas as pd
from PyQt5.QtWidgets import QInputDialog

class BaseAnalysis():
    def __init__(self, experiments,  data, name = None, image = None, **kwargs):
        
        self.name = name
        if name is None:
            name, ok = QInputDialog.getText(self, 'Input Name', 'Please input the name of the analysis')
            if not ok:
                return
        self.experiments = experiments
        self.data = data
        self.image = image

        for karg in kwargs:
            setattr(self, karg, kwargs[karg])

        self.dictionary = {'Name': self.name,
                           'Experiments': self.experiments,
                           'Data': self.data,
                           'Image': self.image}
        
        for karg in kwargs:
            self.dictionary[karg] = kwargs[karg]

    def get_dictionary(self) -> dict:
        return self.dictionary
    
    def get_data(self) -> dict:
        return {f'{self.name}_data': self.data}

    
    def __repr__(self):
        return f'Analysis name: {self.name}\nList of experiments: {self.experiments}\n'


# Definiujemy unikalny typ dla poziomów Twojego MultiIndexu


class OverpotentialAnalysis(BaseAnalysis):
    IndexLevel = Literal['Sample', 'Cycle', 'Experiment']
    def __init__(self, name: str, experiments: list, data: pd.DataFrame, **kwargs):
        super().__init__(name = name, experiments = experiments, data = data, **kwargs)

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
    
    def get_data(self):
        return {f'{self.name}_OVERPOTENTIALS': self.data}
    
class DoubleLayerAnalysis(BaseAnalysis):
    def __init__(self, name: str, experiments: list, fitting_data: pd.DataFrame, raw_data: pd.DataFrame, **kwargs):
        # Przekazujemy fitting_data jako główny "data" do bazy, albo odwrotnie - zależnie od preferencji.
        # Umówmy się, że głównym 'data' będą punkty surowe, a fitting_data przypiszemy jawnie.
        super().__init__(experiments = experiments, name = name, data=raw_data, **kwargs)
        

        # Dzięki kwargs, jeśli podasz `potential=chosen_potential`, 
        # automatycznie w klasie bazowej zrobi się self.potential = chosen_potential

        self.fitting_data = fitting_data
        self.dictionary['Fitting data'] = self.fitting_data
        
    def get_data(self):
        return {f'{self.name}_CDL_Fit': self.fitting_data,
                f'{self.name}_CDL_Parameters': self.data}
    

class ChronopointAnalysis(BaseAnalysis):
    def __init__(self, name: str, experiments: list, data: pd.DataFrame, **kwargs):
        super().__init__(name, experiments, data, **kwargs)

    def get_data(self):
        return {f'{self.name}_CHRONOPOINTS': self.data}
    

class TafelAnalysis(BaseAnalysis):
    def __init__(self, name: str, experiments: list, data: pd.DataFrame, fitting_data:pd.DataFrame, **kwargs):
        super().__init__(name, experiments, data, **kwargs)

        self.fitting_data = fitting_data
    def get_data(self):
        return {f'{self.name}_TAFEL_SLOPES': self.data,
                f'{self.name}_TAFEL_FITS': self.fitting_data}
    

class MeanAnalysis(BaseAnalysis):
    def __init__(self, name: str, experiments: list, data: pd.DataFrame, selection, **kwargs) -> dict:
    
        super().__init__(name = name, experiments = experiments, data = data, **kwargs)
        self.selection = selection

    def get_data(self):
        return 
    


