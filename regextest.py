import re
import os
from collections import defaultdict

files = os.listdir('input/')

def parse_filename(filename):
    match = re.match(r"(.+?)_(#\d+)(?:_(#\d+))?\.DTA$", filename)
    if match:
        experiment_name = match.group(1)
        experiment_cycle = match.group(2) if match.group(2) else None
        experiment_number = match.group(3) if match.group(3) else None

        return experiment_name, experiment_cycle, experiment_number
    return None

def group_files(filenames):
    """Grupuje pliki według nazwy eksperymentu i pierwszej liczby."""
    grouped = defaultdict(list)
    
    for file in filenames:
        parsed = parse_filename(file)
        if parsed:
            key = (parsed[0], parsed[1])  # (nazwa eksperymentu, pierwsza liczba)
            grouped[key].append(file)
    
    return grouped

x = group_files(files)
print(x)