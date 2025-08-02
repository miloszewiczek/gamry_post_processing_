from os import walk
from os import path
import pandas as pd
import gamry_parser
from pathlib import Path

gp = gamry_parser.GamryParser()
sciezka = path.abspath(input('podaj sciezke: '))
dataframes = {}
for root, dirs, files in walk(sciezka):
    name = path.basename(root)
    dfs = []
    for file in files:
        if 'MYCIE_' in file:
            gp.load(path.join(root,file))
            potential = gp.curves[0]['Vf']
            potential_df = pd.DataFrame(potential)
            current_list = [curve['Im'].reset_index(drop=True) for curve in gp.curves]
            current_df = pd.DataFrame(current_list).T
            current_df
            dfs.append(pd.concat([potential_df, current_df], axis=1))
    if len(dfs) > 1:
        dataframes[f'{name}'] = pd.concat(dfs,axis=1)

with pd.ExcelWriter(path.abspath(sciezka+'output.xlsx'), engine='openpyxl') as writer:  
    for name, data in dataframes.items():
        data.to_excel(writer, sheet_name=f'{name}')
