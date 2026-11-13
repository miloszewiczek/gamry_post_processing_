from contextlib import contextmanager
import numpy as np
import pandas as pd
import matplotlib.cm as cm

from PyQt5.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout, QPushButton, QComboBox, 
    QLabel, QGroupBox, QWidget, QSplitter, QColorDialog, QInputDialog,
    QSpinBox, QDoubleSpinBox, QFileDialog, QMessageBox, QFormLayout
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

from core.experiments import Voltammetry, ECSA
from gui_PtQt.small_widgets import TreeSelectorWithCheckboxes, SimpleDoubleSpinBox, Selector, SelectorWithSample
from gui_PtQt.plotting_area import DoubleLayerCanvas
from core.functions.functions import calculate_ECSA_from_slope
from core import ExperimentManager, analysis_manager
from core.experiments.analysis import DoubleLayerAnalysis
from gui_PtQt.tafel import TafelCoreWidget


class DoubleLayerDialog(QDialog):
    """Tradycyjne okno z drzewem wyboru dla użytkownika."""
    def __init__(self, selected_indices, manager=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Double Layer Capacity & ECSA Calculation")
        self.resize(1550, 760)
        
        # Komponenty
        self.selector = SelectorWithSample(selected_indices)
        self.analysis_widget = DoubleLayerCoreWidget(manager=manager)
        self.analysis_widget.analysis_done.connect(self.selector.mark_as_analyzed)
        
        # Główny layout okna
        main_layout = QHBoxLayout(self)
        
        # Widget-kontener dla lewego panelu (Selektora)
        left_widget = QWidget()
        left_panel = QVBoxLayout(left_widget)
        left_panel.setContentsMargins(0, 0, 0, 0)
        left_panel.addWidget(QLabel("<b>Select Experiments:</b>"))
        left_panel.addWidget(self.selector)
        
        # Splitter horyzontalny
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(self.analysis_widget)
        
        splitter.setSizes([380, 950])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(splitter)
        
        # Łączenie sygnałów
        self.selector.flat_list_signal.connect(self.analysis_widget.set_experiments)
        self.selector.flat_list_signal.connect(self.analysis_widget.enable_next_analysis)


class DoubleLayerCoreWidget(TafelCoreWidget):
    """
    Serce analizy CDL z zachowaną oryginalną strukturą obliczeń,
    wyborem koloru próbki, edycją czcionek (pt) pod Worda oraz eksportem do Excela/LabPlot.
    """
    analysis_done = pyqtSignal()
    
    def __init__(self, manager: ExperimentManager, parent=None):
        self.sample_colors = {}
        super().__init__(manager, parent, canvas_type=DoubleLayerCanvas)
        
        self.default_analysis_prefix = 'CDL'
        self.experiment_dict = {}
        self.fitting_data_list = []
        self.raw_data_list = []
        self.previous_selection = None

    def get_sample_color(self, sample, index=0):
        default_palette = [
            "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", 
            "#9467bd", "#8c564b", "#e377c2", "#000000"
        ]
        if sample not in self.sample_colors:
            self.sample_colors[sample] = default_palette[index % len(default_palette)]
        return self.sample_colors[sample]

    def choose_sample_colors(self):
        if not self.experiment_dict:
            return

        samples = list(self.experiment_dict.keys())
        sample_names = [getattr(s, 'sample_name', getattr(s, 'short_name', str(s))) for s in samples]
        
        chosen_name, ok = QInputDialog.getItem(
            self, "Wybierz próbkę", "Próbka do zmiany koloru:", sample_names, 0, False
        )
        if ok and chosen_name:
            idx = sample_names.index(chosen_name)
            sample = samples[idx]
            cur_color = self.get_sample_color(sample, idx)
            new_color = QColorDialog.getColor(QColor(cur_color), self, f"Kolor dla {chosen_name}")
            if new_color.isValid():
                self.sample_colors[sample] = new_color.name()
                self.replot_selected_curve()
                self.run_cdl_calculation()

    def setup_ui(self):
        from .small_widgets import Tracker

        self.track = Tracker(column_names=['Name', 'Potential', 'Curve'],
                             column_widths=[50, 50, 50],
                             add_delete=True)

        self.potential_spinbox = SimpleDoubleSpinBox(0, None)
        self.curve_combobox = QComboBox()
        self.calculate_btn = QPushButton("Calculate CDL")
        self.add_analysis_btn = QPushButton('Add to Table')
        self.save_analysis_btn = QPushButton('Save Final Analysis')
        
        self.color_btn = QPushButton("Ustaw kolory próbek...")
        self.color_btn.clicked.connect(self.choose_sample_colors)

        # --- KONTROLKI CZCIONKI (PUNKTACJA PT I STYL POD WORDA) ---
        self.font_family_combo = QComboBox()
        self.font_family_combo.addItems(["Arial", "Times New Roman", "Calibri", "Helvetica", "DejaVu Sans"])
        
        self.font_style_combo = QComboBox()
        self.font_style_combo.addItems(["Normalny", "Pogrubiony (Bold)", "Kursywa (Italic)"])

        self.axis_font_spin = QSpinBox()
        self.axis_font_spin.setRange(6, 32)
        self.axis_font_spin.setValue(11)
        self.axis_font_spin.setSuffix(" pt")

        self.tick_font_spin = QSpinBox()
        self.tick_font_spin.setRange(6, 28)
        self.tick_font_spin.setValue(10)
        self.tick_font_spin.setSuffix(" pt")

        self.title_font_spin = QSpinBox()
        self.title_font_spin.setRange(6, 36)
        self.title_font_spin.setValue(12)
        self.title_font_spin.setSuffix(" pt")

        self.export_excel_btn = QPushButton("Eksportuj CDL + CV do Excela (LabPlot)")
        self.export_excel_btn.setStyleSheet("background-color: #15803D; color: white; font-weight: bold; padding: 5px;")
        self.export_excel_btn.clicked.connect(self.export_cdl_and_cv_to_excel)

        self.export_img_btn = QPushButton("Zapisz wykres CV/CDL (300 DPI Word)")
        self.export_img_btn.clicked.connect(self.save_figure_for_word)

        self.calculate_btn.setStyleSheet("font-weight: bold; padding: 5px;")
        self.save_analysis_btn.setStyleSheet("background-color: #2a75ad; color: white; font-weight: bold; padding: 5px;")

        self.connect_signals()

        main_layout = QHBoxLayout(self)
        
        # --- LEWY PANEL KONTROLNY ---
        control_widget = QWidget()
        control_layout = QVBoxLayout(control_widget)
        control_layout.setContentsMargins(0, 0, 0, 0)
        
        settings_group = QGroupBox("Plotting & Analysis Settings")
        settings_group.setMaximumWidth(340) 
        
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignLeft)
        form_layout.addRow(QLabel("Curve Index:"), self.curve_combobox)
        form_layout.addRow(QLabel("Potential [V]:"), self.potential_spinbox)
        form_layout.addRow(QLabel("Krój czcionki:"), self.font_family_combo)
        form_layout.addRow(QLabel("Styl czcionki:"), self.font_style_combo)
        form_layout.addRow(QLabel("Podpisy osi [pt]:"), self.axis_font_spin)
        form_layout.addRow(QLabel("Liczby osi [pt]:"), self.tick_font_spin)
        form_layout.addRow(QLabel("Tytuł/Legenda [pt]:"), self.title_font_spin)
        
        settings_layout = QVBoxLayout(settings_group)
        settings_layout.addLayout(form_layout)
        settings_layout.addSpacing(6)
        settings_layout.addWidget(self.calculate_btn)
        settings_layout.addWidget(self.add_analysis_btn)
        settings_layout.addWidget(self.color_btn)
        
        settings_layout.addSpacing(10)
        settings_layout.addWidget(QLabel("<b>Saved Points Tracker:</b>"))
        settings_layout.addWidget(self.track)
        
        settings_layout.addSpacing(6)
        settings_layout.addWidget(self.save_analysis_btn)
        settings_layout.addWidget(self.export_excel_btn)
        settings_layout.addWidget(self.export_img_btn)
        self.save_analysis_btn.clicked.connect(self.create_analysis)
        
        control_layout.addWidget(settings_group)
        control_layout.addStretch()

        # --- PRAWY PANEL (WYKRES) ---
        canvas_widget = QWidget()
        canvas_layout = QVBoxLayout(canvas_widget)
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        canvas_layout.addWidget(self.canvas)
        canvas_layout.addWidget(self.canvas.toolbar)

        internal_splitter = QSplitter(Qt.Horizontal)
        internal_splitter.addWidget(control_widget)
        internal_splitter.addWidget(canvas_widget)
        internal_splitter.setSizes([340, 820])
        internal_splitter.setCollapsible(0, False)
        
        main_layout.addWidget(internal_splitter)

    def connect_signals(self):
        self.curve_combobox.currentIndexChanged.connect(self.replot_selected_curve)
        self.curve_combobox.currentIndexChanged.connect(self.enable_next_analysis)

        self.calculate_btn.clicked.connect(self.run_cdl_calculation)
        self.potential_spinbox.valueChanged.connect(self.canvas.move_vline)
        self.potential_spinbox.valueChanged.connect(self.enable_next_analysis)
        self.add_analysis_btn.clicked.connect(self.add_data)

        # Sygnały natychmiastowej aktualizacji czcionki na wykresach CV i CDL
        self.font_family_combo.currentTextChanged.connect(self.apply_font_settings)
        self.font_style_combo.currentTextChanged.connect(self.apply_font_settings)
        self.axis_font_spin.valueChanged.connect(self.apply_font_settings)
        self.tick_font_spin.valueChanged.connect(self.apply_font_settings)
        self.title_font_spin.valueChanged.connect(self.apply_font_settings)

    def apply_font_settings(self):
        """Stosuje wybrany rozmiar czcionki (pt) i krój do wykresów CV i CDL."""
        if not hasattr(self, 'canvas') or not hasattr(self.canvas, 'figure'):
            return

        family = self.font_family_combo.currentText()
        style_txt = self.font_style_combo.currentText()
        weight = 'bold' if 'Pogrub' in style_txt else 'normal'
        fstyle = 'italic' if 'Kursyw' in style_txt else 'normal'

        label_pt = self.axis_font_spin.value()
        tick_pt = self.tick_font_spin.value()
        title_pt = self.title_font_spin.value()

        for ax in self.canvas.figure.axes:
            if ax.get_title():
                ax.set_title(ax.get_title(), fontname=family, fontsize=title_pt, fontweight=weight, fontstyle=fstyle)
            ax.set_xlabel(ax.get_xlabel(), fontname=family, fontsize=label_pt, fontweight=weight, fontstyle=fstyle)
            ax.set_ylabel(ax.get_ylabel(), fontname=family, fontsize=label_pt, fontweight=weight, fontstyle=fstyle)

            for tick in ax.get_xticklabels() + ax.get_yticklabels():
                tick.set_fontname(family)
                tick.set_fontsize(tick_pt)
                tick.set_fontweight(weight)
                tick.set_fontstyle(fstyle)

            leg = ax.get_legend()
            if leg is not None:
                for txt in leg.get_texts():
                    txt.set_fontname(family)
                    txt.set_fontsize(max(6, title_pt - 1))
                    txt.set_fontweight(weight)
                    txt.set_fontstyle(fstyle)

        try:
            self.canvas.figure.tight_layout()
        except Exception:
            pass
        self.canvas.draw_idle()

    @contextmanager
    def signals_blocked(self, widget):
        widget.blockSignals(True)
        try:
            yield
        finally:
            widget.blockSignals(False)

    def enable_next_analysis(self):
        self.calculate_btn.setEnabled(True)

    def set_experiments(self, experiments):
        self.experiments = experiments
        self.experiment_dict = self.manager.construct_tree_with_cycles(experiments)

        num_samples = len(self.experiment_dict.keys())
        try:
            self.cmap = cm.get_cmap('Set1', max(num_samples * 2, 1))
        except AttributeError:
            import matplotlib.pyplot as plt
            self.cmap = plt.colormaps['Set1'].resampled(max(num_samples * 2, 1))

        self.refresh_ui_state()

    def refresh_ui_state(self):
        available_curves = self.get_common_curve_indices()

        if not self.experiments or not available_curves:
            with self.signals_blocked(self.curve_combobox):
                self.previous_selection = self.curve_combobox.currentText()
                self.curve_combobox.clear()
                self.curve_combobox.setCurrentText('Add an experiment to analysis')
                self.curve_combobox.setDisabled(True)
                self.calculate_btn.setDisabled(True)
            self.canvas.clear_all()
            return

        self.curve_combobox.setDisabled(False)
        self.calculate_btn.setDisabled(False)
        
        with self.signals_blocked(self.curve_combobox):
            self.curve_combobox.clear()
            self.curve_combobox.addItems(available_curves)

            if self.previous_selection in available_curves:
                self.curve_combobox.setCurrentText(self.previous_selection)
            elif available_curves:
                current_max_item = self.curve_combobox.count()
                self.curve_combobox.setCurrentIndex(current_max_item - 1)
                
        self.replot_selected_curve()
        
        first_exp = self.experiments[0] if self.experiments else None
        if first_exp and hasattr(first_exp, 'get_half_potential'):
            x = first_exp.get_half_potential()
            with self.signals_blocked(self.potential_spinbox):
                self.potential_spinbox.setValue(x)
            self.canvas.move_vline(x)
            
    def replot_selected_curve(self):
        self.canvas.clear_except_line()

        raw_text = self.curve_combobox.currentText()
        if raw_text and raw_text.isdigit() and self.experiment_dict:
            selected_curve = [int(raw_text)]

            for s_idx, (sample, cycle_dict) in enumerate(self.experiment_dict.items()):
                color = self.get_sample_color(sample, s_idx)
                for i, (cycle_num, experiments) in enumerate(cycle_dict.items()):
                    data_to_plot = {experiment: experiment.get_plot_data(selected_curve) for experiment in experiments}
                    self.canvas.plot_cv_curves(data_to_plot, color=color)

            self.apply_font_settings()

    def get_current_indexes(self):
        raw_text = self.curve_combobox.currentText()
        if raw_text and raw_text.isdigit():
            return [int(raw_text)]
        return None

    def get_common_curve_indices(self):
        if not self.experiments:
            return []
        
        lengths = [len(exp.data_list) for exp in self.experiments if hasattr(exp, 'data_list')]
        if not lengths:
            return []
            
        min_len = min(lengths)
        return [str(i) for i in range(min_len)]

    def run_cdl_calculation(self):
        """Pobiera parametry, liczy nachylenie i rysuje prawy wykres z zabezpieczeniem przed NoneType."""
        if not self.experiments or not self.experiment_dict:
            return

        self.canvas.ax_cdl.clear()            
        chosen_potential = self.potential_spinbox.value()
        current_index = self.get_current_indexes()
        if current_index is None:
            return

        multi_index_tuples = []
        fitting_data = []
        data = []
        new_dict = {}

        for s_idx, (sample, cycle_dict) in enumerate(self.experiment_dict.items()):
            color = self.get_sample_color(sample, s_idx)
            new_dict[sample] = {}

            for i, (cycle_num, experiments) in enumerate(cycle_dict.items()):
                new_dict[sample][cycle_num] = {}
                
                try:
                    results_dict = calculate_ECSA_from_slope(
                        ECSA_experiments=experiments, 
                        potential=chosen_potential, 
                        index=current_index
                    )
                except Exception:
                    results_dict = None

                if results_dict and isinstance(results_dict, dict):
                    if 'df_fitting' in results_dict and 'df_data' in results_dict:
                        self.canvas.plot_cdl_fit("", results_dict, color=color)

                        mi_tuple = (sample.user_tag, sample.sample_name, cycle_num, chosen_potential)
                        multi_index_tuples.append(mi_tuple)
                        fitting_data.append(results_dict['df_fitting'])
                        data.append(results_dict['df_data'])

        if fitting_data and data:
            names = ('Tag', 'Sample', 'Cycle', 'Potential [V]')
            self.fitting_data = pd.concat(fitting_data, axis=0)
            self.fitting_data.columns.names = ['Parameter']
            multiindex = pd.MultiIndex.from_tuples(multi_index_tuples, names=names)
            self.fitting_data.index = multiindex

            self.raw_data = pd.concat(data, axis=1, keys=multi_index_tuples, names=names)

            self.calculate_btn.setDisabled(True)
            self.add_analysis_btn.setEnabled(True)
        else:
            self.calculate_btn.setEnabled(True)
            self.add_analysis_btn.setDisabled(True)

        self.apply_font_settings()

    def add_data(self):
        if hasattr(self, 'fitting_data'):
            self.fitting_data_list.append(self.fitting_data)
            self.raw_data_list.append(self.raw_data)

            data_to_store = (self.raw_data, self.fitting_data)

            columns = ['Test', 
                       str(self.potential_spinbox.value()),
                       self.curve_combobox.currentText()]
            self.track.add_row(columns=columns, data=data_to_store)
            self.add_analysis_btn.setDisabled(True)
            
            self.analysis_done.emit()

    def join_data(self, data: list[pd.DataFrame], axis=0):
        if data is not None:
            joined_data = pd.concat(data, axis=axis)
            return joined_data

    def create_analysis(self):
        raw_data, fitting_data = self.track.get_data()

        if raw_data and fitting_data:
            name = analysis_manager.ask_for_analysis_name(self.default_analysis_prefix)
            if name:
                joined_raw_data = self.join_data(raw_data, axis=1)
                joined_fitting_data = self.join_data(fitting_data, axis=0)
                data = {'Raw Data': joined_raw_data,
                        'Fitting Data': joined_fitting_data}
                cdl_analysis = DoubleLayerAnalysis(
                    name=name, 
                    data=data,
                )   
                analysis_manager.add_analysis(cdl_analysis)

    def export_cdl_and_cv_to_excel(self):
        """Zapisuje wyliczone punkty CDL oraz krzywe CV jako kolumny X i Y do pliku Excel pod LabPlot."""
        if not self.experiment_dict:
            QMessageBox.information(self, "Brak danych", "Najpierw wybierz eksperymenty i oblicz CDL.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Eksportuj wyniki CDL i krzywe CV do Excela (LabPlot)",
            "Wyniki_CDL_oraz_CV_LabPlot.xlsx", "Pliki Excel (*.xlsx)"
        )
        if not file_path:
            return

        try:
            raw_list, fit_list = self.track.get_data()
            if fit_list and raw_list:
                df_fit = self.join_data(fit_list, axis=0)
                df_raw = self.join_data(raw_list, axis=1)
            elif hasattr(self, 'fitting_data') and hasattr(self, 'raw_data'):
                df_fit = self.fitting_data
                df_raw = self.raw_data
            else:
                self.run_cdl_calculation()
                df_fit = getattr(self, 'fitting_data', pd.DataFrame())
                df_raw = getattr(self, 'raw_data', pd.DataFrame())

            # Zbieranie krzywych CV (X i Y) dla wybranego cyklu
            cv_columns = {}
            max_len = 0
            selected_curve = self.get_current_indexes() or [0]
            temp_series = []

            for sample, cycle_dict in self.experiment_dict.items():
                s_name = getattr(sample, 'sample_name', str(sample))
                for cycle_num, experiments in cycle_dict.items():
                    for exp in experiments:
                        plot_df = exp.get_plot_data(selected_curve)
                        if isinstance(plot_df, list) and len(plot_df) > 0:
                            plot_df = plot_df[0]
                        if isinstance(plot_df, pd.DataFrame) and plot_df.shape[1] >= 2:
                            x_vals = plot_df.iloc[:, 0].values
                            y_vals = plot_df.iloc[:, 1].values
                            label = f"{s_name}_{getattr(exp, 'file_name', 'CV')}"
                            temp_series.append((label, x_vals, y_vals))
                            max_len = max(max_len, len(x_vals))

            for label, x_vals, y_vals in temp_series:
                x_pad = np.full(max_len, np.nan)
                y_pad = np.full(max_len, np.nan)
                x_pad[:len(x_vals)] = x_vals
                y_pad[:len(y_vals)] = y_vals
                cv_columns[f"X_Potential_{label}"] = x_pad
                cv_columns[f"Y_Current_{label}"] = y_pad

            df_cv_xy = pd.DataFrame(cv_columns)

            with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
                if not df_fit.empty:
                    df_fit_clean = df_fit.reset_index()
                    if isinstance(df_fit_clean.columns, pd.MultiIndex):
                        df_fit_clean.columns = ["_".join(str(c) for c in col if str(c)) for col in df_fit_clean.columns.values]
                    df_fit_clean.to_excel(writer, sheet_name="CDL_Wyniki_Nachylenie", index=False)

                if not df_raw.empty:
                    df_raw_clean = df_raw.copy()
                    if isinstance(df_raw_clean.columns, pd.MultiIndex):
                        df_raw_clean.columns = ["_".join(str(c) for c in col if str(c)) for col in df_raw_clean.columns.values]
                    df_raw_clean.reset_index(drop=True).to_excel(writer, sheet_name="CDL_Prosta_XY_LabPlot", index=False)

                if not df_cv_xy.empty:
                    df_cv_xy.to_excel(writer, sheet_name="CV_Krzywe_XY_LabPlot", index=False)

            QMessageBox.information(
                self, "Zapisano pomyślnie",
                f"Zapisano wyniki CDL oraz krzywe CV do pliku:\n{file_path}\n\n"
                "Arkusze z kolumnami X i Y możesz bezpośrednio wkleić do aplikacji LabPlot."
            )
        except Exception as e:
            QMessageBox.critical(self, "Błąd eksportu", f"Nie udało się zapisać pliku Excel:\n{e}")

    def save_figure_for_word(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Zapisz wykres CV/CDL (300 DPI pod Worda)",
            "Wykres_CDL_CV_Word.png", "Obraz PNG 300 DPI (*.png);;Dokument PDF (*.pdf)"
        )
        if file_path:
            self.apply_font_settings()
            self.canvas.figure.savefig(file_path, dpi=300, bbox_inches='tight')
            QMessageBox.information(self, "Zapisano wykres", f"Zapisano wykres w jakości 300 DPI:\n{file_path}")