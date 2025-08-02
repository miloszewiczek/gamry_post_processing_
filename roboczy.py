
from defines import Collection_Manager, Experiment_Collection, Experiment
from defines import *


Files = GetFilesFromFolder('input')
Manager = Collection_Manager()
for file in Files:
    Exp = LoadFile(file)
    Manager.Add_Experiment(Exp)

x = Manager.List_Collections()
