
import gamry_parser as parser
import pandas as pd
import numpy as np
from numpy.polynomial.polynomial import polyfit
import glob
import os
import re
from itertools import chain
from itertools import product
import matplotlib.pylab as pl
import matplotlib.style
import sys
import matplotlib.pyplot as plt
from matplotlib.backend_bases import MouseButton
from tkinter import Tk 
from tkinter.filedialog import askopenfilenames
import typing
import time
from math import pi

def get_filenames():
    Tk().withdraw()
    filenames = askopenfilenames()
    path = filenames[0]
    path = path[0:path.rfind('/')]
    return filenames, path

def get_area(area, i):
    
    area_val = input('Please input the sample area: \n1. 0.196 cm2 (big RedoxMe) \n2. 0.125 cm2 (small RedoxMe) \n3. Custom area \n4. Area by diamter\n')
    if i == 3:
        print("Jeszcze raz się pomylisz, kurwo...")
    elif i == 4:
        print("Nie mam do Ciebie sił...")
    elif i == 5:
        print("... Ostatni raz...")
    elif i == 6:
        print("Chuj ci w dupę.")
        sys.exit()
    try:
        area_val = int(area_val)
    except ValueError:
        i = i+1
        get_area(area, i)
    if int(area_val) - 1 in [0,1]:
        area_val = area[area_val - 1]
        return area_val
    elif int(area_val) - 1 == 2:
        try:
            area_val = float(input('Please input custom area in [cm2]\n'))
            return area_val
        except ValueError:
            print('\nPlease enter a float value! Restarting.')
            i++1
            get_area(area, i)
    elif int(area_val) - 1 == 3:
        try:
            diameter = float(input('Please input diameter in [mm]\n'))    
            area_val = pi*diameter**2/(4*100)
        except ValueError:
            print('\nPlease enter a proper diameter value! Restarting.')
            i++1
            get_area(area, i)
        return area_val
    else:
        get_area(area)

def get_cs():
    print('''Please input specific capacitance of the sample in [mF/cm2]. 
Based on [1] it should be in the range of 0.015-0.110 [mF/cm2] in H2SO4 and 0.022-0.130 [mF/cm2] in NaOH/KOH solutions.
        1. 0.035 (default up-to-date) or any other key
        2. Custom value
--------------------------------------------------------------------------
[1] McCrory et. al Benchmarking Heterogenous Electrocatalysts for the Oxygen Evolution Reaction (2013)
--------------------------------------------------------------------------\n''')
    while True:
        ans = input()
        try:
            ans = int(ans)
            if ans == 1:
                c_specific = 0.035
                print(f'Cs set to {c_specific} [mF/cm2]\n')
                return c_specific
            elif ans == 2:
                c_specific = float(input('''Specific capactinace value:\n'''))
                print(f'Cs set to {c_specific} [mF/cm2]\n')
                return c_specific
        except ValueError:
            if ans == '':
                c_specific = 0.035
                print(f'Cs set to {c_specific} [mF/cm2]\n')
                return c_specific
            
            print('Please provide proper input (int/Enter key for default)\n')
            time.sleep(1)
            print('''Please input specific capacitance of the sample in [mF/cm2]:
        1. 0.035 (default up-to-date) or any other key
        2. Custom value''')
            continue


def get_offset():
    while True:
        try:
            E_offset = input('''Please choose the offset potential:
    1. (def) AgCl: 0.21 [V]
    2. Ag: 0.35 [V]
    3. Custom offset\n''')
            E_offset = int(E_offset)
            if E_offset > 3 or E_offset < 1:
                print('Please input an integer in range\n')
                continue
            elif E_offset == 1:
                E_offset = 0.21
            elif E_offset == 2:
                E_offset = 0.35
            elif E_offset == 3:
                try:
                    E_offset = float(input('''Please input custom offset potential:\n'''))
                except ValueError:
                    continue
            return E_offset
        except ValueError:
            if E_offset == '':
                E_offset = 0.21
                print(f'Offset potential set to default value of 0.21 [V]\n')
                return E_offset
            print('Please input an integer\n')
            continue
    
def get_di_E(ecsa_file):

    gp.load(ecsa_file[0])
    header = gp.get_header()
    v_in = header['VINIT']*1000
    v_1 = header['VLIMIT1']*1000
    v_2 = header['VLIMIT2']*1000
    v_out = header['VFINAL']*1000
    while True:
        print(f'''The ECSA range potentials setup:\n
        {v_in} -> ({v_1} <-> {v_2})x{int(header['CYCLES'])} -> {v_out}  [mV]
''')
        try:
            di_E = float(input('''Please input the potential to calculate ECSA from in [mV]\n'''))
    
        except ValueError:
            print('Please input correct data type (int/float)\n')
            continue
        if di_E > (max(v_1, v_2)) or di_E < min((v_1, v_2)):
            print('Please input potential from the range!\n')
            continue
        return di_E
        
def set_units():
    dic = {"1":['m',1000], "2":["µ",1E6], "3":["",1]}
    E_unit = dic["1"]
    I_unit= dic["1"]
    # E_unit = dic[input("Please select units for potential: 1. mV, 2. µV, 3. V.\n")]
    # I_unit = dic[input("Please select units for current: 1. mA, 2. µA, 3. A.\n")]
    
    return E_unit, I_unit

def sort(files_list):

    #takes files in the folder iteratively and sorts them in respective 
    #containers depending on TITLE/TEST IDENTIFIER

    fs = {}
    for f in files_list:
        
        #CHCECKS FOR SIZE OF THE FILE. IF ITS 0, IT SKIPS THE FILE
        check_file = os.stat(f).st_size
        if check_file == 0:
                name = f[:f.rfind("/")]
                print(f'File {name}')
                continue
        
        #REGEX SEARCH FOR THE CYCLE NUMBER
        result = re.search("#[1-9]_#",f)
        if result is None:

            #IF A SINGLE CYCLE - IT'S SINGLE MEASRUEMENT, ASSIGNS IT TO A LIST AND THEN THE FILE IS APPENDED
            if "SINGLE MEASUREMENT" not in fs:
                fs["SINGLE CYCLE MEASUREMENT"] = []
        
            fs["SINGLE CYCLE MEASUREMENT"].append(f)
        else:
            #CREATES A KEY 'CYCLE <NUMBER>' AND ADDS THE FILE TO THE CYCLE
            if "CYCLE "+ result.group(0)[1] not in fs:
                fs["CYCLE "+result.group(0)[1]] = []
            
            fs["CYCLE "+result.group(0)[1]].append(f)
    

    #LOOP FOR DIVIDING THE EXPERIMENTS FROM CYCLES INTO BUCKETS - NESTED DICTIONARY
    #THE DIVISION IS BASED ON THE HEADER['TITLE'] - THE IDENTIFIER TAG
    for cycle in fs.keys():
    
        f_sorted = {}

        for f in fs[cycle]: 
            
            #LOADS THE FILE INTO PARSER
            gp.load(f)

            #LOADS THE HEADER AND ASSIGNS IT TO THE VARIABLE 'header'
            header = gp.get_header()

            #GETS THE TAG AND NAME OF THE EXPERIMENT FROM FILE HEADER - header['TITLE']
            if re.search("ECSA|RF|AREA", header["TITLE"], re.IGNORECASE):
                if "ECSA" not in f_sorted:
                    f_sorted["ECSA"] = []
                f_sorted["ECSA"].append(f)
            elif re.search("HER|OER|LSV|AKTYWNOSC|Linear|CAT", header["TITLE"], re.IGNORECASE):
                if "HER" not in f_sorted:
                    f_sorted["HER"] = []
                f_sorted["HER"].append(f)
            elif re.search("OER", header["TITLE"], re.IGNORECASE):
                if "OER" not in f_sorted:
                    f_sorted["OER"] = []
                f_sorted["OER"].append(f)
            elif re.search("STABILITY|Chronoamperometry Scan", header["TITLE"], re.IGNORECASE):
                if "CHRONOA" not in f_sorted:
                    f_sorted["STABILITY"] = []
                f_sorted["STABILITY"].append(f)
            elif re.search("EIS|EISPOTEN", header["TITLE"], re.IGNORECASE):
                if "EIS" not in f_sorted:
                    f_sorted["EIS"] = []
                f_sorted["EIS"].append(f)
            elif re.search("CHRONOP|CHRONOA", header["TITLE"], re.IGNORECASE):
                if "CHRONOP" not in f_sorted:
                    f_sorted["CHRONOP"] = []
                f_sorted["CHRONOP"].append(f)
            else:
                if "OTHER" not in f_sorted:
                    f_sorted["OTHER"] = []
                f_sorted["OTHER"].append(f)
        
        fs[cycle] = f_sorted
    return fs

def create_ecsa_dfs(ecsa_files):
        global Ru_cycle
        Ru_cycle = ecsa_files[1]
        print('Calculating ECSA...')

        res = list(map(calc_ecsa, ecsa_files[0]))
        print('Calculating ECSA...DONE')

        cv, ecsa = (zip(*res))
        ecsa = pd.DataFrame(ecsa, columns = ["Scanrate", "dj", 'dj_err'])

        #POLYFIT - LINEAR REGRESSION, TO GET THE SLOPE - y = ax + b
        b, a = polyfit(ecsa["Scanrate"], ecsa["dj"], 1)
        
        #ROUGHNESS FACTOR. IT'S ECSA DIVIDED BY THE GEOMETRIC AREA
        ecsa['C_DL/area [mF/cm2]'] = a/area
        ecsa['Ru [Ohm]'] = Ru_cycle
        ecsa['E_di [mV]'] = di_E
        return cv, ecsa, (b,a)
    
def calc_ecsa(f):
    
# =============================================================================
# TAKES IN A FILEPATH (f) AND LOADS IT INTO THE GAMRYPARSER     
# RETURNS MODIFIED CURVES DATAFRAMES INTO A LIST
# =============================================================================
    
    # p STANDS FOR PARAMETERS, cs IS FOR CURVES
    # FINAL OUTPUT IS AN EXCEL FILE WHERE ALL OF THE DATA IS AGGREGATED IN DIFFERENT SHEETS
    # IN CASE OF ECSA - WE HAVE TWO DIFFERENT SHEETS. ONE FOR CYCLIC VOLTAMMETRY CURVES (cs)
    # AND THE OTHER, CONTAINING DATA OF DELTA_I vs SCAN RATE OF THE MEASUREMENT IN (p)
    p, cs = [ ], [ ]
    gp.load(f)
    curves = gp.get_curves()
    header = gp.get_header()
    
    #THERE IS A GAMRY SOFTWARE BUG WHERE THE LAST MEASUREMENT IS A SINGLE POINT, WHICH IS UNWANTED THIS GETS RID OF IT.
    if len(curves[-1].index) == 1:
        curves = curves[:-1]

    #THIS VARIABLE IS IMPORTANT FOR THE p list FROM WHICH FINAL DATAFRAME IS CONSTRUCTED (SCANRATE VS DELTA_I)    
    scan_rt = header["SCANRATE"]
    
    #THE FOLLOWING LOOP IS INTRODUCED AS SOMETIMES A SINGLE 'ECSA' MEASUREMENT CONSISTS OF 3 DIFFERENT CURVE.
    #THIS IS MAINLY FOR STATISTICS AND STANDARD ERROR ASSESMENT.
    for curve in curves:
        
        # E_OFFSET MEANS THE STANDARD POTENTIAL OF A REFERENCE 
        # ELECTRODE, GIVEN AS A GLOBAL INPUT

        #MULTIPLTYING TO GET UNITS DEFINED BY USER
        curve["Vf"] *= units[1][1]
        curve["Im"] *= units[0][1]
        #DATA PROCESSING - NAMELY IR-DROP CORRECTION,
        #GEOMETRICAL CURRENT DENSITY (CURRENT DIVIDED BY GEOMETRICAL AREA - area)
        curve["Vf_iR"] = curve["Vf"] - curve["Im"] * Ru_cycle
        curve["Im_GEO"] = curve["Im"]/area
        curve = curve[["Vf", "Vf_iR", "Im", "Im_GEO"]]
        curve = curve.reset_index(drop = True)
        curve.insert(0, "SCANRATE", np.nan)
        curve.at[0, 'SCANRATE'] = scan_rt
        
        
        # di CALCULATES THE DIFFERENCE BETWEEN TWO POINTS CLOSEST 
        # TO PICKED POTENTIAL FOR ECSA, GIVEN BY USER INPUT (di_E)
        
        di = curve.iloc[(curve["Vf"]-di_E).abs().argsort()[:2]]
        di = di.diff()
        p.append(np.abs((di.at[di.index[1],"Im"])))
        cs.append(curve)
        
        
    #RETURNS THE MIDDLE CURVE, HOWEVER THERE IS ROOM FOR IMPROVEMENT - THE USER COULD GET VISUALIZATIONS FIRST
    #AND THEN PICK THE CURVE
    return [cs[-2]], (scan_rt, np.mean(p), np.std(p) ) 
    

def other_dfs(i, data):
    global Ru_cycle

    #THIS FUNCTION TAKES IN CYCLE NUMBER (i) AND LIST OF FILE NAMES CORRESONDING TO AN EXPERIMENT (data)
    #AND MODIFIES THEM DEPENDING ON THE EXPERIMENT TYPE (SEE modify_cs function BELOW)

    #i IS ALSO USED TO INDICATE WHETHER THE EXCEL FILE EXISTS OR IT NEEDS TO BE CREATED.
    #IT IS USED IN THE save_to_excel function BELOW VIA PROXY save_mode
    if i == 0:
        save_mode = 'w'
    else:
        save_mode = 'a'
    
    #ECSA IS CALCULATED AS CDL [F/cm^2] WHICH IS THE SLOPE OF LINEAR REGRESSION (a in y = ax + b), WHERE x - SCANRATE, y - delta_I
    #THIS SLOPE IS THEN DIVIDED BY SPECIFIC CAPACITANCE TO OBTAIN ECSA MEASURED IN [cm^2]
    ecsa = data[0][1]/c_specific

    #TAKES THE Ru VALUE PROVIDED BY THE USER FOR EACH CYCLE. 
    #THIS WILL BE DEPRECATED IN FUTURE VERSIONS, I DECIDED THAT TWO DIFFERENT Ru VALUES ARE A BAD IDEA. INSTEAD, 1 IS ENOUGH
    Ru_cycle = Ru[i]
    cycle = data[1]
    exps = data[2]

    #UNPACKS THE LIST OF LISTS INTO A SINGLE LIST OF CURVE DATAFRAMES
    cv = list(chain.from_iterable(data[3]))
    to_ecsa = []
    
    #THIS IS THE scan_rate vs Delta_I DATAFRAME, WHICH HAS ITS OWN EXCEL SHEET
    #THE ECSA FILES ARE TAKEIN INTO ACCOUNT FIRST, BECAUSE THE NEXT EXPERIMENTS NEED TO BE NORMALIZED TO THE ECSA VALUE
    to_ecsa = [ data[4]]

    save_to_excel(cycle, "CV", save_mode,  cv)
    save_mode = 'a'
    save_to_excel(cycle, "ECSA", save_mode, to_ecsa)
    for exp, files in exps.items():
        
        if exp == "ECSA":
           continue 
        data_exp = [] 
        print(f'    Modifying {exp}...')
        for file in files:
            data_exp.append(modify_cs(exp, ecsa, file))
        if exp == "HER" or exp == "OER":    

            #THIS IS QUITE A BURDEL I'D SAY. THIS DEFINITELY NEEDS TO BE IMPROVED FOR VISUAL AND COMPUTATIONAL SAKE
            #r IS A LIST OF ALL THE CURVES, CONTAINS p and t
            results = list(zip(*data_exp))
            overpots = list(chain.from_iterable(results[1]))
            lsv_tafel_dfs = list(zip(*results[0]))
            lsv_dfs = list(chain.from_iterable(lsv_tafel_dfs[0]))
            tafel_dfs = list(chain.from_iterable(lsv_tafel_dfs[1]))
            plot_LSV(axes, 1,i, lsv_dfs)
            plot_TAFEL(axes, 2,i, tafel_dfs)
            save_to_excel(cycle, "LSV", save_mode,  lsv_dfs)
            save_to_excel(cycle, "TAFEL", save_mode,  tafel_dfs)
            overpots = pd.concat(overpots,axis=1)
            overpots['Mean'] = overpots.mean(axis=1)
            overpots['Stdv'] = overpots.std(axis=1)
            overpots['Overpotentials'] = ov_col
            overpots.set_index('Overpotentials', inplace= True)
            
            overpots = [overpots]
            save_to_excel(cycle, "OVERPOTENTIALS", save_mode, overpots)
            
        elif exp == "EIS":
            results = list(chain.from_iterable(data_exp))

            #3, i - ROW AND COLUMN IN THE GRAPH
            plot_EIS(axes,3,i, results)
            save_to_excel(cycle, exp, save_mode, results)
        elif exp == "CHRONOP" or exp == 'CHRONOA' or exp == 'STABILITY':
            results = list(zip(*data_exp))

            data = results[1]
            d = pd.DataFrame(data, columns=['Vf_iR','Im_GEO','Im_ECSA'])

            if exp == 'STABILITY':
                #0, 1 - ROW AND COLUMN IN THE GRAPH
                full = results[0][0][0]
                plot_CHRONOA(axes, 0, 1, full)
                save_to_excel(cycle, exp, save_mode, [full])        
            else:   
                plot_CSV(axes, 4,i,d)
                save_to_excel(cycle, exp, save_mode, [d])
            
            # save_to_excel(cycle, "STABILITY", save_mode, full)
        print(f'    Modifying {exp}...DONE')

        
        

def modify_cs(exp,ecsa,file):
    
    #MAIN FUNCTION FOR MODIFYING EXPERIMENT DATA EXCEPT FOR ECSA, WHICH HAD TO BE PROCESSED FIRST
    #TAKES THE EXPERIMENT TAG (exp), ECSA VALUE (ecsa) AND FILE PATH (file)
    #OUTPUTS MODIFIED LIST OF DATAFRAMES

    #LOADS THE FILE INTO THE PARSER
    gp.load(file)
    curves = gp.get_curves()
    header = gp.get_header()
    
    #GETS RID OF THE SINGLE-POINT CURVE
    if len(curves[-1].index) == 1:
        curves = curves[:-1]

    #cs AND p ARE CONTAINERS FOR CURVES AND PARAMETERS
    cs, p = [ ], [ ]

    #UNUSED VARIABLES FOR "CHRONOP" TAG
    #scv = [ ]
    #y_data = []

    
    if exp == "HER" or exp == "OER":
        
        #TAFEL CURVES
         t_cs = [ ]
         
         #MIGHT BE 1+ CURVES IN THE FILE
         for curve in curves:
             
             #MODIFYING POTENTIAL TO THE RHE SCALE, BY ADDING THE E_offset
             curve["Vf"] += E_offset

             #SAME AS BEFORE, MODIFIES UNITS, INTRODUCES 
             curve["Vf"] *= units[1][1]
             curve["Im"] *= units[0][1]

             curve["Vf_iR"] = curve["Vf"] - curve["Im"] * Ru_cycle
             curve["Im_GEO"] = curve["Im"] / area
             
             #NORMALIZING TO ECSA, CHECKS IF IT IS PRESENT
             if isinstance(ecsa, float):
                 curve["Im_ECSA"] = curve["Im"] / ecsa
                 curve = curve[["Vf", "Vf_iR", "Im_ECSA", "Im_GEO"]]
             else:   
                 curve = curve[["Vf", "Vf_iR", "Im_GEO"]]
             curve.reset_index(drop = True)
            
            #CREATING AND MODIFYING TAFEL CURVES
            #BASICALLY ALL CURRENT DENSITIES ARE LOGARITHMED
             t_curve = curve.copy()
             if isinstance(ecsa, float):
                 tmp = t_curve.pop("Im_ECSA")
                 t_curve.insert(0, "log10 Im_ECSA", tmp)
                 t_curve["log10 Im_ECSA"] = np.log10(np.abs(t_curve["log10 Im_ECSA"]))
             
             tmp = t_curve.pop("Im_GEO")
             t_curve.insert(0, "log10 Im_GEO", tmp)
             t_curve["log10 Im_GEO"] = np.log10(np.abs(t_curve["log10 Im_GEO"]))
             
             curve.insert(0,"File", np.nan)
             curve.loc[:,"File"] = ""
             curve.loc[0, "File"] = file[file.rfind("\\"):]
             
             t_curve.insert(0,"File", np.nan)
             t_curve.loc[:,"File"] = ""
             t_curve.loc[0, "File"] = file[file.rfind("\\"):]
             
             cs.append(curve)
             t_cs.append(t_curve)
             
             p.append(calc_ov(curve, len(curves)))
             
             return (cs, t_cs), p
         
    elif exp == "EIS":
         
         for curve in curves:
             
             curve = curve[["Freq", "Zreal", "Zimag"]]
             curve.insert(0,'V DC [V]', np.nan)
             curve.at[0, 'V DC [V]'] = header["VDC"]
             cs.append(curve)
            
        
         return cs
     
    elif exp == "CHRONOP" or exp == "CHRONOA" or exp == "STABILITY":
        
         for curve in curves:
             
             curve["Vf"] += E_offset
             curve["Vf"] *= units[1][1]
             curve["Im"] *= units[0][1]
             curve["Vf_iR"] = curve["Vf"] - curve["Im"] * Ru_cycle
             curve["Im_GEO"] = curve["Im"] / area
             
             tmp = {'x':'','y':''}

             '''THIS IS A FUNCTION FOR CLICKING THE POINTS ON GRAPH. HAD TO BE REMOVED DUE TO COLLISION WITH THE MAIN GRAPH'''
            #  def on_click(event):
            #     if event.button is MouseButton.LEFT:
            #         x = event.xdata
            #         y = event.ydata
            #         plt.close()
            #         tmp['x'],tmp['y'] = x,y
            #         return 
            #  fig2 = plt.figure(2)
            #  fig2.set_size_inches(10,10)
             
            #  plt.scatter(curve["T"],curve["Im"])
            #  plt.connect('button_press_event', on_click)
            #  plt.show()

             potential = curve["Vf_iR"].iloc[-1]
             if isinstance(ecsa, float):
                 curve["Im_ECSA"] = curve["Im"] / ecsa
                 curve = curve[["T","Vf", "Vf_iR", "Im_ECSA", "Im_GEO"]]
                 csv_point = (curve["Im_GEO"].iloc[-1],curve["Im_ECSA"].iloc[-1])
             else:   
                 curve = curve[["T","Vf", "Vf_iR", "Im_GEO"]]
                 csv_point = (curve["Im_GEO"].iloc[-1])
             
             cs.append(curve)
         return cs, (potential,)+csv_point
         
def calc_ov(curve, n_cs):
    
# =============================================================================
#     RETURNS OVERPOTENTIAL AT CURRENTS NORMALIZED
#     TO ECSA AND GEO. THE OVS VALUES CAN BE PERSONALIZED
#     VIA INI CONFIG
# =============================================================================

    ovs = [ ]
    
    
    for key, value_list in ov_dict.items():
        
        for v in value_list:
            
            if n_cs > 1:
                
                for i in range(n_cs):
                    
                   tmp = curve.iloc[(curve[f'Im_{key}'] - v).abs().argsort()[:2]]
                if iR_bool == 0:
                   ovs.append(tmp["Vf"].reset_index(drop = True))
                elif iR_bool == 1:
                   ovs.append(tmp["Vf_iR"].reset_index(drop = True))  
            
            else:
                
                tmp = curve.iloc[(curve[f'Im_{key}'] - v).abs().argsort()[:1]]
                if iR_bool == 0:
                    ovs.append(tmp["Vf"].reset_index(drop = True))
                elif iR_bool == 1:
                    ovs.append(tmp["Vf_iR"].reset_index(drop = True))
    
    
    
    return pd.DataFrame(ovs)

        
def plot_ecsa(axes,x,y, ecsa, p):
    
    
    
    axarr = axes[x,y]
    axarr.set_title("ECSA")
    axarr.set_xlabel(r'$dEdt^{-1}$' + f'$[{{{units[0][0]}}}V$'+'$s^{-1}]$')
    axarr.set_ylabel(r'$\Delta i\ $' + f'[${{{units[1][0]}}}A]$')
    
    for i, (p, df) in enumerate(zip(p, ecsa)):
        label =f'Cycle {i}: {p[1]:.1e} $[{{{units[1][0]}}} F$'
        x, y, y_err = df["Scanrate"], df["dj"], df["dj_err"]
        xticks = np.arange(min(x),max(x)+1, 10)
        
        axarr.plot(x, x *p[1] + p[0],  label = label)
        axarr.errorbar(x, y, yerr = y_err, fmt = ".", marker = '.',)
        axarr.set_xticks(ticks = xticks)
        
        
    axarr.legend(loc = 'upper left')
        
    
    return axes

def plot_LSV(axes, row, col, LSV_dfs):
    
    
    axarr = axes[row,col]
    axarr.set_title("LSV")
    axarr.set_xlabel(r'$E\ vs\ RHE\ $' + f'$[{{{units[0][0]}}}V]$')
    axarr.set_ylabel(r'$j_{GEO}\ $' + f'[${{{units[1][0]}}}A$' + '$cm^{-2}]$')
    axarr2 = axarr.twinx()
    axarr2.set_ylabel(r'$j_{ECSA}\ $' + f'[${{{units[1][0]}}}A$' + '$cm^{-2}]$')
    
    for i, df in enumerate(LSV_dfs):
        label = f'{i+1}'
        if iR_bool == 1:
            x = df["Vf_iR"]
        else:
            x = df["Vf"]
        y, y2 = df["Im_GEO"], df["Im_ECSA"]
        axarr.plot(x, y,  label = label)
        axarr2.plot(x, y2, )
    axarr.legend(loc = 'upper left')
    
def plot_TAFEL(axes, row, col, TAFEL_dfs):
    
    axarr = axes[row,col]
    axarr.set_title("TAFEL ANALYSIS")
    axarr.set_xlabel('$log_{10}j_{ECSA}$' + f'[${{{units[1][0]}}}A$' + '$cm^{-2}]$')
    axarr.set_ylabel(r'$E\ vs\ RHE\ $' + f'$[{{{units[0][0]}}}V]$')

    
    for i, df in enumerate(TAFEL_dfs):
        label = f'{i+1}'
        x, x2, y = df['log10 Im_ECSA'], df["log10 Im_GEO"], df["Vf_iR"]
        axarr.plot(x2, y,   label = label)
    axarr.legend(loc = 'upper left')
    
def plot_EIS(axes, row, col, EIS_dfs):
    
    axarr = axes[row,col]
    axarr.set_title("Potentiostatis EIS")
    axarr.set_xlabel(r'$Zprim$' +r'$[\Omega]$')
    axarr.set_ylabel(r'$-Zbis$' + r'$[\Omega]$')
    
    for i, df in enumerate(EIS_dfs):
        label = f'{i+1}'
        x, y = df['Zreal'], -df['Zimag']
        axarr.scatter(x,y, s=5, label = label)
    axarr.legend(loc = 'upper right')
    axarr.axis('square')


def plot_CHRONOA(axes, row, col, CHRONOA_dfs):
    
    axarr = axes[row,col]
    axarr.set_title(f"Chronoamperometry measurement @ 0 V vs RHE")
    axarr.set_xlabel("$Time [s]$")
    axarr.set_ylabel(r'$j_{GEO}\ $' + f'[${{{units[1][0]}}}A$' + '$cm^{-2}]$')
    
    df = CHRONOA_dfs
    x, y = df["T"], df["Im_GEO"]
    axarr.plot(x, y)
    
def plot_CSV(axes, row, col, df):
    
    
    axarr = axes[row,col]
    axarr.set_title(f"Chronoamperometry")
    axarr.set_xlabel("$Potential vs RHE [V]$")
    axarr.set_ylabel(r'$j_{GEO}\ $' + f'[${{{units[1][0]}}}A$' + '$cm^{-2}]$')
    axarr2 = axarr.twinx()
    axarr2.set_ylabel(r'$j_{ECSA}\ $' + f'[${{{units[1][0]}}}A$' + '$cm^{-2}]$')
    axarr.scatter(df['Vf_iR'],df['Im_GEO'])
    axarr2.scatter(df['Vf_iR'],df['Im_ECSA'])

    

def save_to_excel(cycle, experiment, save_mode, *dfs):

    for df_list in dfs:
        
        DF = pd.concat(df_list, axis=1)
        with pd.ExcelWriter(f'{path}/{file_name}.xlsx', mode = save_mode) as writer:
            DF.to_excel(writer, sheet_name = f'{cycle}_{experiment}')
    
def save_cv(cv):
    
    for i, df_list in enumerate(cv):
        DF = pd.concat(df_list, axis=1)
        with pd.ExcelWriter(f'{path}/{file_name}.xlsx', mode = 'w') as writer:
            DF.to_excel(writer, sheet_name = f'Cycle {i}'  )    


def main():

    global units
    global E_offset
    global di_E
    global Ru
    global area
    global ov_dict
    global axes
    global colors
    global file_name
    global iR_bool
    global Ru_cycle
    global c_specific
    global ov_col
    global gp
    global path

    Ru_cycle = ''
    ov_dict = {"GEO":[-10], "ECSA": [-500, -1000, -2000, -4000]}
    ov_col = []
    for k in ov_dict:
        for val in ov_dict[k]:
            ov_col.append(k+str(val))

    E_offset = [0.21, 0.35]
    area = [0.196, 0.125663706143592]



    gp = parser.GamryParser()
    
    while True:
        try:
            fetched_data = int(input("""Welcome to a self-made program for processing data obtained via Gamry potentiostats.
        1. Choose folder with data files
        2. Automatically fetch the data files from current folder\n"""))
        except ValueError:
            print('Please input an integer\n')
            continue
        if fetched_data > 2:
            print('Please input an integer in range\n')
            continue
        if fetched_data == 1:
            print('Select a folder\n')
            sorted_data, path = get_filenames()
            sorted_data = sort(sorted_data)
            print(f'Selected path: {path}\n')
            break
        elif fetched_data == 2:
            
            print('Processing data in current folder...\n')
            f_list = glob.glob('./*DTA')
            path = os.getcwd()
            sorted_data = sort(f_list)
            break

    time.sleep(2)

    c_specific = get_cs()
    E_offset = get_offset()
    di_E = get_di_E(sorted_data['CYCLE 1']['ECSA'])

    area = get_area(area,0)
    iR_bool = int(input("Use normal voltage or iR-dropped one?\n 1. Normal voltage\n 2. iR-dropped\n")) -1
    file_name = input("Please type in name of outputfile:\n")



    units = set_units()
    fig, axes = plt.subplots(nrows = 5, ncols = 2)
    fig.suptitle(f'{file_name}', fontsize = 30)
    plt.subplots_adjust(left=0.1,
                        bottom=0.1, 
                        right=0.9, 
                        top=0.9, 
                        wspace=0.4, 
                        hspace=0.4)

    ecsa_fs = {cycle:sorted_data[cycle]["ECSA"] for cycle in sorted_data}
    Ru=[]

    for n,cycle in enumerate(sorted_data):
        
        R_val = re.findall(r'(\d+(?:\.\d+)?)', input(f'Please input Ru values in Ohm for Cycle {n+1}.\n The input can be a series of values separated by a space e.g. 1.0  2.0  3.4\n'))
        Ru.append(np.mean(list(map(float, R_val))))
        
    res = list(map(create_ecsa_dfs, zip(ecsa_fs.values(),Ru)))
    cv, ecsa, p = zip(*res)
    ecsa = tuple(ecsa)
    print('Plotting ECSA...')

    #THE 0,0 ARGUMENTS ARE THE POSITIONS ON THE GRAPH
    plot_ecsa(axes,0,0, ecsa, p)
    print('Plotting ECSA...DONE')

    print('Packaging data for other experiments...')
    data_zip = list(zip(p, sorted_data.keys(), sorted_data.values(), cv, ecsa))
    print('Packaging data for other experiments...DONE')
    p = []
    for i, cycle in enumerate(data_zip):
        print(f'Modifying other experiments in cycle {i}...')
        other_dfs(i, cycle)
        print(f'Modifying other experiments in cycle {i}...DONE')
        i++1

    print('Saving figure...')
    fig.savefig(f'{path}/{file_name}.png')
    print('Saving figure...DONE')
    
    restart = int(input('''Process another sample or close the program?
        1. Modify another sample
        2. Close the program\n'''))
    if restart == 1:
        print('Restarting program...')
        main()
    else:
        return


plt.rcParams['figure.figsize'] = [15,15]
plt.rcParams['figure.dpi'] = 200
main()
    
