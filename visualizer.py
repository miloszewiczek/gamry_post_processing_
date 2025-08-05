import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import defaultdict

class VisualizerWindow:
    def __init__(self, master, experiments: list):
        self.master = master
        self.experiments = experiments
        self.tree_data = self.build_tree_data()
        self.dataframes = self.collect_processed_data()

        self.master.title("Experiment Visualizer")
        self.setup_gui()

    def setup_gui(self):
        # Treeview (left panel)
        self.tree = ttk.Treeview(self.master, selectmode='extended')
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Matplotlib canvas (right panel)
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.master)
        self.canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Plot button
        self.plot_button = tk.Button(self.master, text="Plot Selected", command=self.plot_selected)
        self.plot_button.pack(side=tk.BOTTOM)

        self.exit_button = tk.Button(self.master, text = 'Exit', command = self.master.destroy)
        self.exit_button.pack(side=tk.BOTTOM)

        self.clear_plots_button = tk.Button(self.master, text = 'Clear plots', command = self.clear_plots)
        self.clear_plots_button.pack(side=tk.BOTTOM)

        # Populate the tree view
        self.populate_tree()

    def build_tree_data(self):
        tree = defaultdict(lambda: defaultdict(set))
        for exp in self.experiments:
            exp.load_data()
            exp.process_data()
            structure = exp.get_tree_structure()
            for path, curves in structure.items():
                for curve, params in curves.items():
                    tree[path][curve].update(params)
        # Convert sets to lists for consistency
        return {k: {kk: list(vv) for kk, vv in v.items()} for k, v in tree.items()}

    def collect_processed_data(self):
        df_dict = {}
        for exp in self.experiments:
            if hasattr(exp, "processed_data"):
                df_dict[exp.file_path] = exp.processed_data
        return df_dict

    def populate_tree(self):
        for path, curves in self.tree_data.items():
            file_node = self.tree.insert('', 'end', text=path, open=True)
            for curve, params in curves.items():
                curve_node = self.tree.insert(file_node, 'end', text=curve, open=True)
                for param in params:
                    self.tree.insert(curve_node, 'end', text=param)

    def clear_plots(self):
        self.ax.clear()

    def plot_selected(self):
        selected_items = self.tree.selection()
        if not selected_items:
            return

        self.ax.clear()

        for item in selected_items:
            path_node = self.tree.parent(self.tree.parent(item))
            curve_node = self.tree.parent(item)
            param_node = item

            if not path_node or not curve_node or not param_node:
                continue

            file_path = self.tree.item(path_node)['text']
            curve = self.tree.item(curve_node)['text']
            param = self.tree.item(param_node)['text']

            df = self.dataframes.get(file_path)
            if df is None:
                continue

            try:
                levels = df.columns.nlevels

                if levels == 3:
                    x = df.loc[:, (file_path, curve, 'E vs RHE [V]')]
                    y = df.loc[:, (file_path, curve, param)]
                elif levels == 2:
                    x = df.loc[:, (file_path, 'E vs RHE [V]')]
                    y = df.loc[:, (file_path, param)]
                else:
                    x = df['E vs RHE [V]']
                    y = df[param]

                self.ax.plot(x, y, label=f'{file_path} - {curve} - {param}')
            except KeyError as e:
                print(f"Missing: {e}")
                continue

        self.ax.set_xlabel('E vs RHE [V]')
        self.ax.set_ylabel('Parameter')
        self.ax.grid(True)
        self.ax.legend()
        self.canvas.draw()
