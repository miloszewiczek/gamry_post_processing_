from core.functions.utilities import previous_program_add_ecsa_curve
from collections import defaultdict
import pandas as pd
from pathlib import Path

list_of_files = []

while True:
    inpt = input('Enter File Path: ')
    if inpt == '':
        break
    list_of_files.append(inpt)

cycle_dict = defaultdict(list)
for file in list_of_files:
    result = previous_program_add_ecsa_curve(file)
    for cycle, dataframe in result.items():
        cycle_dict[cycle].append(dataframe)
    
with pd.ExcelWriter(Path(list_of_files[0]).parent / f'{Path(list_of_files[0]).name.split('.')[0]}_ANALYSIS.xlsx', engine = 'openpyxl', mode = 'w') as writer:
    for cycle, dataframes in cycle_dict.items():
        final_df = pd.concat(dataframes, axis = 1)
        im = final_df.xs("Im_ECSA", axis=1, level=1)
        final_df[('Statisitcs','mean')] = im.mean(axis = 1)
        final_df[('Statisitcs','std')] = im.std(axis = 1)
        final_df.to_excel(writer, sheet_name = cycle)
    