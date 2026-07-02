import pandas as pd
import numpy as np
from typing import List, Literal, Union, Dict, Any
import pandas as pd
from PyQt5.QtWidgets import QInputDialog

class BaseAnalysis():
    def __init__(self, data: dict, name = None, **kwargs):
        
        self.name = name
        if not isinstance(data, dict):
            self.data = {'Data 1': data}
        else:
            self.data = data
        self.dictionary = {}

        if name is None:
            self.name, ok = QInputDialog.getText(None, 'Input Name', 'Please input the name of the analysis')
            if not ok:
                return
        
        for karg in kwargs:
            self.dictionary[karg] = kwargs[karg]

    def get_dictionary(self) -> dict:
        return self.dictionary
    
    def get_data(self) -> dict:
        return self.data
    
    def __repr__(self):
        return f'Analysis name: {self.name}'


# Definiujemy unikalny typ dla poziomów Twojego MultiIndexu


class OverpotentialAnalysis(BaseAnalysis):
    def __init__(self, name:dict, data:dict, **kwargs):
        super().__init__(name = name, data = data, **kwargs)

    
class DoubleLayerAnalysis(BaseAnalysis):
    def __init__(self, name:dict, data:dict, **kwargs):
        super().__init__(name = name, data = data, **kwargs)
        

class ChronopointAnalysis(BaseAnalysis):
    def __init__(self, name:dict, data:dict, **kwargs):
        super().__init__(name = name, data = data, **kwargs)
        

class TafelAnalysis(BaseAnalysis):
    def __init__(self, name:dict, data:dict, **kwargs):
        super().__init__(name = name, data = data, **kwargs)
        

class MeanAnalysis(BaseAnalysis):
    def __init__(self, name:dict, data:dict, **kwargs):
        super().__init__(name = name, data = data, **kwargs)
        
    


