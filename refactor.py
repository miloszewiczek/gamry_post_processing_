from exp_manager import ExperimentManager, ECSA, Experiment, Chronoamperometry, LinearVoltammetry, OpenCircuit, Voltammetry, calculate_ECSA_from_slope, batch_integrate_ECSA, calculate_ECSA_difference, ask_user
import os
from config import messages, config
from datetime import datetime
import numpy as np
import pandas as pd
from tkinter.filedialog import askopenfilenames

'''
manager = ExperimentManager()
files = os.listdir('input/ECSA_test/')

for file in files:
   manager.create_experiment(f'input/ECSA_test/{file}')
   
print(manager.experiments_v2)

y = manager.filter_experiments(object_type=ECSA)
print(y)
options = {"GEO": [-5, -10, -15], "potential": [0.1, 0.2, 0.15], "time":12000}

#name= input('please input name for saving: ')
#manager.save_experiment(tmp, f'{name}', options=options)
'''

def main(key='', interactive = True):
   manager = ExperimentManager()

   while True:
      manager.print_current_status()
      print('0. Testing functions')
      print('1. Dodaj eksperymenty')
      print('2. Filtruj eksperymenty')
      print('3. Procesuj wyfiltrowane eksperymenty')
      print('4. Wylicz CDL')
      print('5. WIP')
      print('6. WIP')
      print('7. ECSA Differences')
      

      if interactive == True:
          option = input()
      else:
          option = key

      match option:
         case '0':
            files = [os.path.join('input/',file) for file in os.listdir('input/') if os.path.isfile(os.path.join('input/',file))]
            for file in files:
                manager.create_experiment(file)
            result = manager.filter_experiments(name = input('Name: '))
            df_tmp = manager.batch_process_selected_experiments(result)
            x = manager.combine_experiment(df_tmp)
            x.to_excel('Combined.xlsx',engine='openpyxl')

         case '1':
            print('Choose a folder\n')
            files = askopenfilenames()
            for file in files:
               manager.create_experiment(file)
         case '2':
               name_input = input(messages['input_messages']['file_name_input']).split() or None

               cycle_input = input(messages['input_messages']['cycle_input'])
               cycle_input = [int(x) for x in cycle_input.split() if x.strip().isdigit()] if cycle_input else None

               object_type_input = input(messages['input_messages']['object_type_input']).strip() or None

               result = manager.filter_experiments(name = name_input, cycle = cycle_input, object_type = object_type_input)
               manager.list_items(result)
         case '3':
              df_tmp = manager.batch_process_selected_experiments()
              save_name = ask_user(messages['input_messages']['save_name'], str)
              manager.save_experiment(file_name = save_name)
         case '4':
              result = manager.filter_experiments(object_type=ECSA)
              df_tmp = manager.batch_process_selected_experiments(result)
              print(df_tmp)

         case '5':
              result = manager.filter_experiments(object_type = LinearVoltammetry)
              df_tmp = manager.batch_process_selected_experiments(result)
              print(df_tmp)
         
         case '6':
              for opt, value in config['default_settings'].items():
                  print(opt, value)

         case '7':
              
              result = manager.filter_experiments(object_type=ECSA)
              differences = calculate_ECSA_difference(result, 0.255, False, False)
              #integrals,slopes = differences[1], differences[2]
              #print(f'Najbliższa dla całki: {integrals}\n Najbliższa dla slopeów: {slopes}.')

              #nazwa = input('Nazwa pliku: ') + '.csv'
              #differences[0].to_csv(nazwa)

if __name__ == '__main__':
    main()





'''
final_df = []
final = []
for root, dirs, files in os.walk(os.path.abspath(input('Gib path: '))):
    manager = ExperimentManager()
    ecsa_files = [os.path.join(root,file) for file in files if 'CV_ECSA' in file]
    for file in ecsa_files:
        manager.create_experiment(file)
    if len(manager.experiments_v2) > 0:
     result = manager.filter_experiments(object_type=ECSA)
     diffs, new = calculate_ECSA_difference(result, 0.15, False, False)
     prefix = os.path.basename(root)
     diffs.index = [prefix+'_1', prefix+'_2']
     final_df.append(diffs)
     if os.path.exists('result.xlsx'):
         mode = 'a'
     else:
         mode = 'w'
     with pd.ExcelWriter('result.xlsx', engine='openpyxl', mode=mode) as writer:
         new.to_excel(writer, sheet_name=prefix[0:30])
final_df = pd.concat(final_df)

final_df.to_excel(f'{input('Nazwa pliku: ')}.xlsx')

'''
     
