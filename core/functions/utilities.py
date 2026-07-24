import pandas as pd
import gamry_parser
from os import path
from tkinter.filedialog  import askopenfilenames

def convert_to_zview(EIS_files = None):
    if EIS_files is None:
        EIS_files = askopenfilenames()
    gp = gamry_parser.GamryParser()
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

    for file in EIS_files:
        normalized_path = path.abspath(file)
        print('Converting: ', normalized_path)
        gp.load(normalized_path)
        print('Loaded: ', normalized_path)
        df = gp.curves[0]
        try:
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
        except:
            print(f'Wrong file type {file}. Skipping')
            continue

        print('Successfully created z60 DataFrame')
        print('Attempting to write header lines')
        
        with open(f'{file[0:file.rfind('.')]}.z60', 'w', newline='') as f:
            for line in header_lines:
                f.write(line + "\n")
            print('Writing DataFrame to csv')
            new_df.to_csv(f, index = False, sep = ',', lineterminator='\n')


def previous_program_add_ecsa_curve(file, 
                                    cv_sheets:list[str] = ['CYCLE 1_ECSA', 'CYCLE 2_ECSA'], 
                                    lsv_sheets:list[str] = ['CYCLE 1_LSV', 'CYCLE 2_LSV']):
    from pathlib import Path
    
    try:
        file_path = Path(file)
    except:
        return 'Invalid path'
    
    file_name = file_path.name.split('.')[0]
    
    cv_dict = pd.read_excel(file_path, sheet_name = cv_sheets)
    lsv_dict = pd.read_excel(file_path, sheet_name = lsv_sheets)

    ecsa_values = []
    for sheet_name, ecsa_dataframe in cv_dict.items():
        try:
            ecsa_value = ecsa_dataframe.loc[0, 'ECSA [cm2]']
            try:
                area = ecsa_dataframe.loc[0, 'area [cm2]']
            except:
                area = ecsa_dataframe.loc[0, 'area']
        except:
            ecsa_value = None
            print('No ECSA!')
        ecsa_values.append(ecsa_value)
    
    final_dict = {}
    for ecsa_val, (sheet_name, lsv_dataframe) in zip(ecsa_values, lsv_dict.items()):
        cols = [lsv_dataframe.iloc[:, i] for i, col in enumerate(lsv_dataframe.columns) if "Im_GEO" in col]
        result = [col / ecsa_val * area for col in cols]
        result.insert(0, lsv_dataframe.loc[:, 'Vf_iR'])
        result_df = pd.concat(result, axis = 1)
        new_cols = []
        for column in result_df.columns:
            if 'GEO' in column:
                new_cols.append('Im_ECSA')
            else:
                new_cols.append(column)

        result_df.columns = new_cols
        result_df.columns = pd.MultiIndex.from_product(
    [[file_name], result_df.columns]
)
        final_dict[sheet_name] = result_df

    return final_dict


        