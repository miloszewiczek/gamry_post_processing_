import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class InteractivePlotApp(tk.Tk):
    def __init__(self, data):
        super().__init__()
        self.title("Interactive Vertical Line Plot")
        self.geometry("800x600")
        self.data = data

        # Simulated data
        self.x = data.processed_data[0]['E vs RHE [V]']
        self.y = data.processed_data[0]['J_GEO [A/cm2]']

        # Create figure
        self.fig, self.ax = plt.subplots()
        self.line, = self.ax.plot(self.x, self.y, label="Data")

        vline_min, vline_max = self.x.min(), self.x.max()
        vline_position = vline_min + (vline_max - vline_min)/2
        self.vline = self.ax.axvline(x=vline_position, color='red', linestyle='--', label="Slider Position")
        self.markers, = self.ax.plot([], [], 'ro')  # multiple points

        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")
        self.ax.legend()

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.draw()

        # Label for info
        self.info_label = ttk.Label(self, text="X: 0.0 | Y: 0.0")
        self.info_label.pack(pady=5)

        # Slider
        self.slider = ttk.Scale(self, from_=self.x.min(), to=self.x.max(), orient='horizontal', command=self.on_slider_move, value = vline_position)
        self.slider.pack(fill=tk.X, padx=20, pady=10)

        #Button to calculate difference
        self.button = ttk.Button(self, text = 'Calculate difference!', command = self.calculate_difference)
        self.button.pack()
        self.difference_info_label = ttk.Label(self, text = "0")
        self.difference_info_label.pack()
        
        #Initiation of the slider so that it's at the middle by default
        self.on_slider_move(vline_position)

    def on_slider_move(self, val):
        val = float(val)
        self.vline.set_xdata([val,val])

        # Get nearest index
        idx = np.searchsorted(self.x, val)
        tolerance = (self.x.max() - self.x.min()) / len(self.x)  # one "step"
        mask = np.abs(self.x - val) < tolerance
        y_vals = self.y[mask]
        x_vals = self.x[mask]
        self.y_vals = y_vals

        if len(y_vals) > 0:
            self.markers.set_data(x_vals, y_vals)
            y_str = ", ".join([f"{y:.4f}" for y in y_vals])
            self.info_label.config(text=f"X ≈ {val:.3f} | Y: [{y_str}]")
        else:
            self.markers.set_data([], [])
            self.info_label.config(text=f"X ≈ {val:.3f} | Y: [no match]")

        self.canvas.draw_idle()

    def calculate_difference(self):
        result = self.y_vals.diff().iloc[-1]
        self.difference_info_label.config(text = f"{result}")
        
        return result
    


if __name__ == "__main__":
    app = InteractivePlotApp()
    app.mainloop()