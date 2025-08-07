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
        self.vline = self.ax.axvline(x=0, color='red', linestyle='--', label="Slider Position")
        self.point_marker, = self.ax.plot([], [], 'ro')  # red dot marker

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
        self.slider = ttk.Scale(self, from_=self.x[0], to=self.x[-1], orient='horizontal', command=self.on_slider_move)
        self.slider.pack(fill=tk.X, padx=20, pady=10)

    def on_slider_move(self, val):
        val = float(val)
        self.vline.set_xdata([val,val])

        # Get nearest index
        idx = np.searchsorted(self.x, val)
        if 0 <= idx < len(self.x):
            x_val = self.x[idx]
            y_val = self.y[idx]

            self.point_marker.set_data([x_val], [y_val])
            self.info_label.config(text=f"X: {x_val:.3f} | Y: {y_val:.3f}")

        self.canvas.draw_idle()

if __name__ == "__main__":
    app = InteractivePlotApp()
    app.mainloop()