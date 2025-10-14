import tkinter as tk
from tkinter import ttk
from scipy.signal import find_peaks
import gamry_parser as gp
from matplotlib import pyplot as plt
import numpy as np


parser = gp.GamryParser()
parser.load(r'd:\!UNI\!sci_materials\!doktorat\!wyniki\TESTY\SPE_ferrocyjanozelaziany_test\CV_#1.DTA')

data = parser.get_curves()[0]
x, y = data['Vf'], data['Im']

imax = np.argmax(x)  # turning point index

# split CV
x_anodic, y_anodic = x[:imax+1], y[:imax+1]
x_cathodic, y_cathodic = x[imax:], y[imax:]

# detect anodic peak
anodic_peaks, anodic_info = find_peaks(y_anodic, prominence=1e-7, distance=1)

# now left/right are within the anodic segment only
i_peak = anodic_peaks[0]
left, right = anodic_info['left_bases'][0], anodic_info['right_bases'][0]

x_seg = x_anodic[left:right+1]
y_seg = y_anodic[left:right+1]

baseline = np.linspace(y_anodic[left], y_anodic[right], len(x_seg))
# --- Plot ---
fig, ax = plt.subplots()

# full CV
ax.plot(x, y, label="CV")

# mark the peak
ax.plot(x[i_peak], y[i_peak], "ro", label="Anodic peak")

# highlight integration region
ax.fill_between(x_seg, baseline, y_seg, alpha=0.3, color="orange", label="Integrated area")

# draw baseline
ax.plot(x_seg, baseline, "k--", label="Baseline")

ax.legend()
ax.set_xlabel("Potential (V)")
ax.set_ylabel("Current (A)")
plt.show()

print(f"Integrated anodic peak charge = {charge:.3e} C")