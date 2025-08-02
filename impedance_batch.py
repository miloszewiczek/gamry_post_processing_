from tkinter.filedialog import askdirectory
from impedance.models.circuits import CustomCircuit
from impedance import preprocessing
import matplotlib.pyplot as plt
from impedance.visualization import plot_nyquist
from tkinter import Tk 
import os

circuit = 'R0-La0-p(R1,CPE0)-p(R2,CPE1)'
initial_guess = [0.5, 2E-5, 0.80, 10, 6.825E-3, 0.95, 10, 1E-3, 0.95]
circuit = CustomCircuit(circuit, initial_guess=initial_guess)
print(circuit)

Tk().withdraw()
path = askdirectory()
print(path)
for parent, folder, files in os.walk(path):
    files = [os.path.join(parent,EIS_file) for EIS_file in files if 'EIS_POTENTIAL' in EIS_file]
    print(files)




'''
freq, Z = preprocessing.readGamry('EIS_POTENTIAL_#1_#1.DTA')

circuit.fit(freq, Z)
Z_fit = circuit.predict(freq)
print(circuit)
fig, ax = plt.subplots()
plot_nyquist(Z, fmt='o', scale=10, ax=ax)
plot_nyquist(Z_fit, fmt='-', scale = 10, ax=ax)
plt.legend(['Data','Fit'])
plt.show()
'''