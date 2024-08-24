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



Files = GetFilesFromFolder('input')
Manager = Collection_Manager()
for file in Files:
    Exp = LoadFile(file)
    Manager.Add_Experiment(Exp)
Manager.print_experiments()