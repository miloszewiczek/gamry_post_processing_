import pandas as pd
import gamry_parser
from os import path
from tkinter.filedialog  import askopenfilenames
from glob import glob
from os import walk

gp = gamry_parser.GamryParser()



#files = askopenfilenames()
header_lines = [
    "ZView Calculated Data File: Version 1.1",
    "Raw Data",
    "Sweep Frequency: Control Voltage",
    r'""',
    r'""',
    r'""',
    r'""',
    r'""'
]

def process(EIS_files):
    for file in EIS_files:
        normalized_path = path.abspath(file)
        print('Converting: ', normalized_path)
        gp.load(normalized_path)
        print('Loaded: ', normalized_path)
        df = gp.curves[0]
        new_df = pd.DataFrame({
            'Freq(Hz)': df['Freq'],
            'DCcurr(A)': 0,
            'DCpot(V)': 0,
            'Time(S)': df['Time'],
            'Zprime(Ohm)': df['Zreal'],
            'Zbis(Ohm)': df['Zimag'],
            'GD': 0,
            'X': 0,
            'Y': 0
        })
        print('Successfully created z60 DataFrame')
        print('Attempting to write header lines')
        
        with open(f'{file[0:file.rfind('.')]}.z60', 'w', newline='') as f:
            for line in header_lines:
                f.write(line + "\n")
            print('Writing DataFrame to csv')
            new_df.to_csv(f, index = False, sep = ',', lineterminator='\n')

for root,dirs,files in walk(input('Gib ścieżka: ')):
    print(root)
    print(files)
    files_to_process = [path.join(root,file) for file in files if 'EIS_POTENTIAL' in file]
    process(EIS_files = files_to_process)