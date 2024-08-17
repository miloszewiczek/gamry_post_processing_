from defines import *

def log_modification(func):
    def wrapper(obj, *args, **kwargs):
        # Przed modyfikacją
        print(f"Obiekt o TAGu '{obj.TAG}' jest teraz modyfikowany...")
        
        # Wywołanie oryginalnej funkcji
        result = func(obj, *args, **kwargs)
        
        # Po modyfikacji
        print(f"Modyfikacje dla obiektu o TAGu '{obj.TAG}' zostały skończone.")
        
        return result
    return wrapper

class MyObject:
    def __init__(self, tag, data):
        self.TAG = tag
        self.Data = data

    @log_modification
    def modify_data(self, new_data):
        self.Data = new_data

# Przykładowe użycie
obj = MyObject('TEST123', 'Initial Data')
obj.modify_data('Modified Data')