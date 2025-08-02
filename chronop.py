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

    def load_data(file_path):
        # Replace with your file loading logic

        gp.load(file_path)
        time, potential, current = gp.curves[0]['T'], gp.curves[0]['Vf'], gp.curves[0]['Im']
        return time, potential, current

    def process_file(i):
        full_path = file_list[i]
        file_name = os.path.basename(full_path)
        full_path = os.path.join(data_folder, file_name)
        print(full_path)
        time, potential, current = load_data(full_path)

        fig, ax = plt.subplots()
        line, = ax.plot(time, current, label=file_name)
        selected_point, = ax.plot([], [], 'ro')
        plt.title(f"[{i+1}/{len(file_list)}] Click to select a point in: {data_folder_basename}")
        plt.xlabel("T [s]")
        plt.ylabel("Current [A]")
        ax.legend()

        def onclick(event):
            if event.inaxes != ax:
                return
            x_click = event.xdata
            y_click = event.ydata
            distances = np.sqrt((time - x_click)**2 + (current - y_click)**2)
            idx = np.argmin(distances)
            x_sel = time[idx]
            y_sel = current[idx]
            
            pot_iR = potential[idx] - current[idx]*Ru
            print(pot_iR)

            selected_point.set_data([x_sel], [y_sel])
            fig.canvas.draw()

            # Save point and close plot
            selected_points.append((file_name, pot_iR, x_sel, y_sel))
            print(f"Selected from {file_name}: x = {x_sel}, y = {y_sel}")
            plt.close(fig)

        cid = fig.canvas.mpl_connect('button_press_event', onclick)
        plt.show()

    # Loop over files
    for i in range(len(file_list)):
        process_file(i)

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
