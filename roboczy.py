from defines import *

#x = GetFilesFromFolder('input')
#print(x)
FILEDICT = {"ECSA":r'input\CV_ECSA_#1_#2.DTA',
            "LSV": r'input\test_file.DTA',
            "STABILITY": r'input\CHRONOA_STABILITY_#1_#1.DTA',
            "EIS": r'input\EIS_POTENTIAL_#1_#4.DTA',
            "MYCIE": r'input\MYCIE_#1.DTA',
            "CHRONOP": r'input\CHRONOPOINTS_#1_#8.DTA'}
Filepath = FILEDICT['ECSA']
y = LoadFile(Filepath)
y.Modify_Dataframes(1,0.1)
print(y.Data[0])
x = y.Charge_Integral()
print(x)
l = y.Calculate_CDL_from_slope(0)
print(l)