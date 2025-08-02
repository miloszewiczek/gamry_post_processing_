import matplotlib.pyplot as plt
import numpy as np
import os
from glob import glob
import gamry_parser
import pandas as pd
import re


def extract_two_numbers(filename):
    numbers = re.findall(r'#(\d+)', filename)
    if len(numbers) >= 2:
        cycle = int(numbers[0])
        experiment = int(numbers[1])
        #print(cycle, experiment)
        return (cycle, experiment)
    elif len(numbers) == 1:
        return (int(numbers[0]), 0)
    else:
        return (0,0)
    
def main(data_folder):
    # ======= SETTINGS =======
    
    file_list = glob(data_folder +'/CHRONOPOINT*.DTA')
    file_list = sorted([f for f in file_list], key=extract_two_numbers)
    data_folder_basename = os.path.basename(data_folder)
    # ========================
    Ru = float(input('Please give Ru value in [Ohm]: '))
    gp = gamry_parser.GamryParser()
    selected_points = []  # to store results


    # ======= OUTPUT SECTION =======
    print("\nAll selected points:")
    for fname, pot,x, y in selected_points:
        print(f"{fname}: x = {x:.3f}, y = {y:.3f}")
    df = pd.DataFrame(selected_points, columns= ['Filename','Potential','Time','Current'])
    return df

if __name__ == '__main__':
    for root, dirs, files in os.walk(os.path.abspath(input('Podaj ścieżkę: '))):
        if len(glob(root+'\\CHRONOPOINT*.DTA')) > 0:
            print(root)
            output_df = main(root)
            with pd.ExcelWriter('chronop.xlsx', mode='a', engine='openpyxl') as writer:
                output_df.to_excel(writer, sheet_name =os.path.basename(root))
