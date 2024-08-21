from defines import *

x = GetFilesFromFolder('input')
print(x)
print(x[1])
y = LoadFile(x[1])
print(y)
y.Double_Layer_Capacitance_Integral(1,1)