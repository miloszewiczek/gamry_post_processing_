import os
import numpy as np
import pandas as pd

from PyQt5.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit, QFileDialog,
    QListWidget, QListWidgetItem, QGroupBox, QFormLayout, QMessageBox,
    QColorDialog, QCheckBox, QSplitter, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


PALETA_DOMYSLNA = [
    "#1f77b4", "#d62728", "#2ca02c", "#ff7f0e",
    "#9467bd", "#000000", "#8c564b", "#e377c2", "#17becf"
]


def wyciagnij_xy_z_eksperymentu(exp):
    """Pobiera obrobione kolumny (X, Y) oraz opisy osi z obiektu Experiment."""
    xlabel, ylabel = "E_iR vs RHE [V]", "J_GEO [A/cm2]"

    if hasattr(exp, "get_plot_data"):
        try:
            res = exp.get_plot_data()
            if isinstance(res, list) and len(res) > 0:
                res = res[-1]
            if isinstance(res, pd.DataFrame) and res.shape[1] >= 2:
                num_df = res.select_dtypes(include=[np.number]).dropna()
                if num_df.shape[1] >= 2:
                    xlabel = str(num_df.columns[0])
                    ylabel = str(num_df.columns[1])
                    return num_df.iloc[:, 0].values.copy(), num_df.iloc[:, 1].values.copy(), xlabel, ylabel
            elif isinstance(res, tuple) and len(res) >= 2:
                return np.asarray(res[0], dtype=float).copy(), np.asarray(res[1], dtype=float).copy(), xlabel, ylabel
        except Exception:
            pass

    for attr in ["processed_data", "data", "df", "data_list"]:
        if hasattr(exp, attr):
            val = getattr(exp, attr)
            if isinstance(val, list) and len(val) > 0:
                val = val[-1]
            if isinstance(val, pd.DataFrame):
                num_df = val.select_dtypes(include=[np.number]).dropna()
                if num_df.shape[1] >= 2:
                    cols_up = {c.upper(): c for c in num_df.columns}
                    col_x = next((cols_up[k] for k in cols_up if any(w in k for w in ["RHE", "POTENTIAL", "VF", "E_"])), num_df.columns[0])
                    col_y = next((cols_up[k] for k in cols_up if any(w in k for w in ["GEO", "DENSITY", "CURRENT", "J_", "IM"]) and cols_up[k] != col_x), num_df.columns[1])
                    return num_df[col_x].values.copy(), num_df[col_y].values.copy(), str(col_x), str(col_y)

    if hasattr(exp, "process_data"):
        try:
            exp.process_data()
            if hasattr(exp, "data") and isinstance(exp.data, pd.DataFrame):
                num_df = exp.data.select_dtypes(include=[np.number]).dropna()
                if num_df.shape[1] >= 2:
                    return num_df.iloc[:, 0].values.copy(), num_df.iloc[:, 1].values.copy(), str(num_df.columns[0]), str(num_df.columns[1])
        except Exception:
            pass

    return np.array([]), np.array([]), xlabel, ylabel


class MiniOriginDialog(QDialog):
    """Stabilny Mini Origin bez nakładania bufora na macOS Retina."""

    def __init__(self, selected_experiments=None, manager=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mini Origin – Stylizacja Wykresu (Skala Word pt) & Eksport XY do LabPlot")
        self.resize(1340, 820)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)

        self.manager = manager
        self.serie = []
        self._blokuj_odswiezanie = True

        self._wczytaj_zaznaczone_eksperymenty(selected_experiments or [])
        self._zbuduj_interfejs()

        self._blokuj_odswiezanie = False
        self.odswiez_wykres()

    def _wczytaj_zaznaczone_eksperymenty(self, obiekty):
        lista_exp = []
        for obj in obiekty:
            if hasattr(obj, "experiments"):
                lista_exp.extend(obj.experiments)
            else:
                lista_exp.append(obj)

        self.domyslny_xlabel = "E_iR vs RHE [V]"
        self.domyslny_ylabel = "J_GEO [A/cm2]"

        for idx, exp in enumerate(lista_exp):
            x, y, xl, yl = wyciagnij_xy_z_eksperymentu(exp)
            if len(x) == 0:
                continue
            self.domyslny_xlabel = xl
            self.domyslny_ylabel = yl

            nazwa = getattr(exp, "user_tag", "") or getattr(exp, "file_name", f"Krzywa_{idx+1}")
            if self.manager is not None:
                try:
                    sample = self.manager.find_sample(exp)
                    if sample and getattr(sample, "sample_name", ""):
                        nazwa = f"{os.path.basename(sample.sample_name)} - {getattr(exp, 'file_name', '')}"
                except Exception:
                    pass

            self.serie.append({
                "nazwa": str(nazwa),
                "x": x,
                "y": y,
                "kolor": PALETA_DOMYSLNA[idx % len(PALETA_DOMYSLNA)],
                "styl_linii": "-",
                "grubosc": 1.8,
                "widoczna": True
            })

    def _zbuduj_interfejs(self):
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # ================= LEWY PANEL USTAWIEŃ (PRZEWIJANY) =================
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setMinimumWidth(400)
        left_scroll.setMaximumWidth(440)
        left_scroll.setFrameShape(QFrame.NoFrame)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_scroll.setWidget(left_widget)

        # 1. Lista krzywych
        grp_krzywe = QGroupBox("1. Wybrane krzywe (zaznacz/odznacz widoczność)")
        v_krzywe = QVBoxLayout(grp_krzywe)

        self.lista_widget = QListWidget()
        self.lista_widget.setMinimumHeight(120)
        self.lista_widget.currentRowChanged.connect(self.wybrano_krzywa)
        self.lista_widget.itemChanged.connect(self.zmieniono_widocznosc_krzywej)
        v_krzywe.addWidget(self.lista_widget)

        f_krzywa = QFormLayout()
        self.inp_nazwa = QLineEdit()
        self.inp_nazwa.textEdited.connect(self.zapisz_ustawienia_krzywej)
        f_krzywa.addRow("Nazwa w legendzie:", self.inp_nazwa)

        self.cmb_line_style = QComboBox()
        self.cmb_line_style.addItems(["Ciągła (-)", "Przerywana (--)", "Kropkowana (:)", "Kreska-kropka (-.)"])
        self.cmb_line_style.currentIndexChanged.connect(self.zapisz_ustawienia_krzywej)
        f_krzywa.addRow("Styl linii:", self.cmb_line_style)

        self.spn_line_width = QDoubleSpinBox()
        self.spn_line_width.setRange(0.5, 6.0)
        self.spn_line_width.setSingleStep(0.25)
        self.spn_line_width.setValue(1.8)
        self.spn_line_width.valueChanged.connect(self.zapisz_ustawienia_krzywej)
        f_krzywa.addRow("Grubość linii:", self.spn_line_width)

        btn_kolor = QPushButton("Zmień kolor zaznaczonej krzywej...")
        btn_kolor.setStyleSheet("background-color: #2563EB; color: white; font-weight: bold; padding: 5px;")
        btn_kolor.clicked.connect(self.zmien_kolor)
        f_krzywa.addRow(btn_kolor)

        v_krzywe.addLayout(f_krzywa)
        left_layout.addWidget(grp_krzywe)

        # 2. Czcionki (pt) i rozmiar pod Worda
        grp_font = QGroupBox("2. Czcionka (pt), Styl i Skala pod Worda")
        f_font = QFormLayout(grp_font)

        self.cmb_font_family = QComboBox()
        self.cmb_font_family.addItems(["Arial", "Times New Roman", "Calibri", "Helvetica", "DejaVu Sans"])
        self.cmb_font_family.currentTextChanged.connect(self.odswiez_wykres)
        f_font.addRow("Krój czcionki:", self.cmb_font_family)

        self.cmb_font_style = QComboBox()
        self.cmb_font_style.addItems(["Normalny", "Pogrubiony (Bold)", "Kursywa (Italic)", "Pogrubiona kursywa"])
        self.cmb_font_style.currentTextChanged.connect(self.odswiez_wykres)
        f_font.addRow("Styl podpisów osi:", self.cmb_font_style)

        self.cmb_tick_style = QComboBox()
        self.cmb_tick_style.addItems(["Normalny", "Pogrubiony (Bold)"])
        self.cmb_tick_style.currentTextChanged.connect(self.odswiez_wykres)
        f_font.addRow("Styl liczb na osiach:", self.cmb_tick_style)

        self.spn_label_pt = QSpinBox()
        self.spn_label_pt.setRange(6, 36)
        self.spn_label_pt.setValue(11)
        self.spn_label_pt.setSuffix(" pt")
        self.spn_label_pt.valueChanged.connect(self.odswiez_wykres)
        f_font.addRow("Podpisy osi X/Y:", self.spn_label_pt)

        self.spn_tick_pt = QSpinBox()
        self.spn_tick_pt.setRange(6, 32)
        self.spn_tick_pt.setValue(10)
        self.spn_tick_pt.setSuffix(" pt")
        self.spn_tick_pt.valueChanged.connect(self.odswiez_wykres)
        f_font.addRow("Liczby na osiach:", self.spn_tick_pt)

        self.spn_legend_pt = QSpinBox()
        self.spn_legend_pt.setRange(6, 32)
        self.spn_legend_pt.setValue(10)
        self.spn_legend_pt.setSuffix(" pt")
        self.spn_legend_pt.valueChanged.connect(self.odswiez_wykres)
        f_font.addRow("Legenda i tytuł:", self.spn_legend_pt)

        self.spn_width_cm = QDoubleSpinBox()
        self.spn_width_cm.setRange(5.0, 30.0)
        self.spn_width_cm.setSingleStep(0.5)
        self.spn_width_cm.setValue(15.0)
        self.spn_width_cm.setSuffix(" cm")
        self.spn_width_cm.valueChanged.connect(self.odswiez_wykres)
        f_font.addRow("Szerokość w Wordzie:", self.spn_width_cm)

        self.spn_height_cm = QDoubleSpinBox()
        self.spn_height_cm.setRange(4.0, 25.0)
        self.spn_height_cm.setSingleStep(0.5)
        self.spn_height_cm.setValue(10.0)
        self.spn_height_cm.setSuffix(" cm")
        self.spn_height_cm.valueChanged.connect(self.odswiez_wykres)
        f_font.addRow("Wysokość w Wordzie:", self.spn_height_cm)

        left_layout.addWidget(grp_font)

        # 3. Opisy osi, przelicznik jednostek i siatka
        grp_axes = QGroupBox("3. Podpisy osi, jednostki i wygląd")
        f_axes = QFormLayout(grp_axes)

        self.cmb_y_mult = QComboBox()
        self.cmb_y_mult.addItems(["1x (Oryginalna jednostka)", "1000x (Przelicz A/cm² -> mA/cm²)"])
        self.cmb_y_mult.currentIndexChanged.connect(self.zmieniono_mnoznik_y)
        f_axes.addRow("Skala osi Y:", self.cmb_y_mult)

        self.inp_title = QLineEdit("")
        self.inp_title.textChanged.connect(self.odswiez_wykres)
        f_axes.addRow("Tytuł wykresu:", self.inp_title)

        self.inp_xlabel = QLineEdit(getattr(self, "domyslny_xlabel", "E_iR vs RHE [V]"))
        self.inp_xlabel.textChanged.connect(self.odswiez_wykres)
        f_axes.addRow("Oś X:", self.inp_xlabel)

        self.inp_ylabel = QLineEdit(getattr(self, "domyslny_ylabel", "J_GEO [A/cm2]"))
        self.inp_ylabel.textChanged.connect(self.odswiez_wykres)
        f_axes.addRow("Oś Y:", self.inp_ylabel)

        self.cmb_grid = QComboBox()
        self.cmb_grid.addItems(["Włączona (Przerywana)", "Włączona (Ciągła)", "Wyłączona"])
        self.cmb_grid.currentIndexChanged.connect(self.odswiez_wykres)
        f_axes.addRow("Siatka (Grid):", self.cmb_grid)

        self.cmb_legend_loc = QComboBox()
        self.cmb_legend_loc.addItems([
            "Włączona – Automatycznie (best)",
            "Włączona – Lewy górny róg",
            "Włączona – Prawy górny róg",
            "Włączona – Lewy dolny róg",
            "Włączona – Prawy dolny róg",
            "Wyłączona (Ukryj legendę)"
        ])
        self.cmb_legend_loc.currentIndexChanged.connect(self.odswiez_wykres)
        f_axes.addRow("Legenda:", self.cmb_legend_loc)

        left_layout.addWidget(grp_axes)

        # 4. Przyciski zapisu
        btn_save_excel = QPushButton("Zapisz kolumny X i Y do Excela / CSV (pod LabPlot)")
        btn_save_excel.setStyleSheet("background-color: #15803D; color: white; font-weight: bold; padding: 8px;")
        btn_save_excel.clicked.connect(self.eksportuj_xy_do_pliku)
        left_layout.addWidget(btn_save_excel)

        btn_save_img = QPushButton("Zapisz wykres w skali 1:1 dla Worda (300 DPI)")
        btn_save_img.setStyleSheet("background-color: #2563EB; color: white; font-weight: bold; padding: 8px;")
        btn_save_img.clicked.connect(self.zapisz_obrazek)
        left_layout.addWidget(btn_save_img)

        left_layout.addStretch()
        splitter.addWidget(left_scroll)

        # ================= PRAWY PANEL WYKRESU (WYŚRODKOWANA KARTKA 1:1) =================
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.fig = Figure(figsize=(15.0 / 2.54, 10.0 / 2.54), dpi=100, facecolor="white")
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)
        self.toolbar = NavigationToolbar(self.canvas, self)

        # Umieszczenie płótna w wyśrodkowanym obszarze zapobiega rozjeżdżaniu bufora na macOS Retina
        self.canvas_scroll = QScrollArea()
        self.canvas_scroll.setWidgetResizable(False)
        self.canvas_scroll.setAlignment(Qt.AlignCenter)
        self.canvas_scroll.setStyleSheet("QScrollArea { background-color: #E2E8F0; border: 1px solid #CBD5E1; }")
        self.canvas_scroll.setWidget(self.canvas)

        right_layout.addWidget(self.toolbar)
        right_layout.addWidget(self.canvas_scroll)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(1, 1)

        self._odswiez_liste_widget()
        if self.serie:
            self.lista_widget.setCurrentRow(0)

    def _odswiez_liste_widget(self):
        self.lista_widget.blockSignals(True)
        self.lista_widget.clear()
        for s in self.serie:
            item = QListWidgetItem(s["nazwa"])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if s.get("widoczna", True) else Qt.Unchecked)
            item.setForeground(QColor(s["kolor"]))
            self.lista_widget.addItem(item)
        self.lista_widget.blockSignals(False)

    def zmieniono_widocznosc_krzywej(self, item):
        if self._blokuj_odswiezanie:
            return
        row = self.lista_widget.row(item)
        if 0 <= row < len(self.serie):
            self.serie[row]["widoczna"] = (item.checkState() == Qt.Checked)
            self.odswiez_wykres()

    def wybrano_krzywa(self, row):
        if row < 0 or row >= len(self.serie):
            return
        s = self.serie[row]
        self._blokuj_odswiezanie = True
        self.inp_nazwa.setText(s["nazwa"])
        self.spn_line_width.setValue(float(s["grubosc"]))
        mapa_odwrotna = {"-": 0, "--": 1, ":": 2, "-.": 3}
        self.cmb_line_style.setCurrentIndex(mapa_odwrotna.get(s["styl_linii"], 0))
        self._blokuj_odswiezanie = False

    def zapisz_ustawienia_krzywej(self):
        if self._blokuj_odswiezanie:
            return
        row = self.lista_widget.currentRow()
        if row < 0 or row >= len(self.serie):
            return
        mapa_styli = {0: "-", 1: "--", 2: ":", 3: "-."}
        nowa_nazwa = self.inp_nazwa.text().strip() or f"Krzywa_{row+1}"
        self.serie[row]["nazwa"] = nowa_nazwa
        self.serie[row]["styl_linii"] = mapa_styli.get(self.cmb_line_style.currentIndex(), "-")
        self.serie[row]["grubosc"] = self.spn_line_width.value()

        self.lista_widget.blockSignals(True)
        item = self.lista_widget.item(row)
        if item is not None:
            item.setText(nowa_nazwa)
        self.lista_widget.blockSignals(False)

        self.odswiez_wykres()

    def zmien_kolor(self):
        row = self.lista_widget.currentRow()
        if row < 0 or row >= len(self.serie):
            return
        kolor = QColorDialog.getColor(QColor(self.serie[row]["kolor"]), self, "Wybierz kolor krzywej")
        if kolor.isValid():
            self.serie[row]["kolor"] = kolor.name()
            self._odswiez_liste_widget()
            self.lista_widget.setCurrentRow(row)
            self.odswiez_wykres()

    def zmieniono_mnoznik_y(self, idx):
        obecny_y = self.inp_ylabel.text()
        if idx == 1 and "[A/" in obecny_y:
            self.inp_ylabel.setText(obecny_y.replace("[A/", "[mA/"))
        elif idx == 0 and "[mA/" in obecny_y:
            self.inp_ylabel.setText(obecny_y.replace("[mA/", "[A/"))
        else:
            self.odswiez_wykres()

    def _rysuj_zawartosc_na_figurze(self, fig):
        """Rysuje wykres na przekazanej figurze (zarówno na ekranie, jak i przy eksporcie 300 DPI)."""
        fig.clear()
        fig.patch.set_facecolor("white")
        ax = fig.add_subplot(111)

        family = self.cmb_font_family.currentText()
        styl_txt = self.cmb_font_style.currentText()
        weight = "bold" if "Pogrub" in styl_txt else "normal"
        fstyle = "italic" if "Kursyw" in styl_txt or "kursyw" in styl_txt else "normal"

        tick_weight = "bold" if "Pogrub" in self.cmb_tick_style.currentText() else "normal"

        label_pt = self.spn_label_pt.value()
        tick_pt = self.spn_tick_pt.value()
        legend_pt = self.spn_legend_pt.value()

        mnoznik_y = 1000.0 if self.cmb_y_mult.currentIndex() == 1 else 1.0

        widoczne_serie = [s for s in self.serie if s.get("widoczna", True)]
        for s in widoczne_serie:
            ax.plot(
                s["x"], s["y"] * mnoznik_y,
                color=s["kolor"],
                linestyle=s["styl_linii"],
                linewidth=s["grubosc"],
                label=s["nazwa"]
            )

        if self.inp_title.text().strip():
            ax.set_title(
                self.inp_title.text(),
                fontname=family, fontsize=legend_pt + 1,
                fontweight=weight, fontstyle=fstyle, pad=8
            )

        ax.set_xlabel(self.inp_xlabel.text(), fontname=family, fontsize=label_pt, fontweight=weight, fontstyle=fstyle)
        ax.set_ylabel(self.inp_ylabel.text(), fontname=family, fontsize=label_pt, fontweight=weight, fontstyle=fstyle)

        for tick in ax.get_xticklabels() + ax.get_yticklabels():
            tick.set_fontname(family)
            tick.set_fontsize(tick_pt)
            tick.set_fontweight(tick_weight)
            tick.set_fontstyle("normal")

        grid_idx = self.cmb_grid.currentIndex()
        if grid_idx == 0:
            ax.grid(True, linestyle="--", alpha=0.35)
        elif grid_idx == 1:
            ax.grid(True, linestyle="-", alpha=0.25)
        else:
            ax.grid(False)

        leg_idx = self.cmb_legend_loc.currentIndex()
        if leg_idx < 5 and widoczne_serie:
            mapa_loc = {
                0: "best",
                1: "upper left",
                2: "upper right",
                3: "lower left",
                4: "lower right"
            }
            prop = {"family": family, "size": legend_pt, "weight": "normal", "style": "normal"}
            ax.legend(prop=prop, loc=mapa_loc.get(leg_idx, "best"), frameon=True)

        fig.tight_layout()
        return ax

    def odswiez_wykres(self):
        if self._blokuj_odswiezanie:
            return

        w_in = self.spn_width_cm.value() / 2.54
        h_in = self.spn_height_cm.value() / 2.54

        # Zmiana rozmiaru poprzez natywny widget Qt eliminuje nakładanie bufora na macOS Retina
        base_dpi = getattr(self.fig, "_original_dpi", 100.0)
        target_w = int(round(w_in * base_dpi))
        target_h = int(round(h_in * base_dpi))

        if self.canvas.width() != target_w or self.canvas.height() != target_h:
            self.canvas.setFixedSize(target_w, target_h)

        self.ax = self._rysuj_zawartosc_na_figurze(self.fig)
        self.canvas.draw()
        self.canvas.update()

    def eksportuj_xy_do_pliku(self):
        widoczne_serie = [s for s in self.serie if s.get("widoczna", True)]
        if not widoczne_serie:
            return
        sciezka, _ = QFileDialog.getSaveFileName(
            self, "Zapisz kolumny X i Y pod LabPlot / Excel",
            "Dane_Wykresu_XY_LabPlot.xlsx",
            "Plik Excel (*.xlsx);;Plik CSV rozdzielany tabulatorem (*.csv)"
        )
        if not sciezka:
            return

        mnoznik_y = 1000.0 if self.cmb_y_mult.currentIndex() == 1 else 1.0
        max_len = max(len(s["x"]) for s in widoczne_serie)
        kolumny = {}
        for idx, s in enumerate(widoczne_serie):
            nazwa = s["nazwa"]
            x_pad = np.full(max_len, np.nan)
            y_pad = np.full(max_len, np.nan)
            x_pad[:len(s["x"])] = s["x"]
            y_pad[:len(s["y"])] = s["y"] * mnoznik_y
            kolumny[f"X_{nazwa}"] = x_pad
            kolumny[f"Y_{nazwa}"] = y_pad

        df_out = pd.DataFrame(kolumny)
        if sciezka.lower().endswith(".csv"):
            df_out.to_csv(sciezka, sep="\t", index=False)
        else:
            with pd.ExcelWriter(sciezka, engine="xlsxwriter") as writer:
                df_out.to_excel(writer, sheet_name="Dane_XY_LabPlot", index=False)

        QMessageBox.information(self, "Zapisano dane XY", f"Zapisano kolumny X i Y gotowe do wklejenia w LabPlot:\n{sciezka}")

    def zapisz_obrazek(self):
        sciezka, _ = QFileDialog.getSaveFileName(
            self, "Zapisz wykres w skali Worda (300 DPI)",
            "Wykres_Word_300DPI.png", "Obraz PNG 300 DPI (*.png);;Dokument PDF (*.pdf)"
        )
        if sciezka:
            w_in = self.spn_width_cm.value() / 2.54
            h_in = self.spn_height_cm.value() / 2.54
            # Tworzymy niezależną figurę eksportową 300 DPI, aby nie zmieniać DPI ekranu Retina
            fig_export = Figure(figsize=(w_in, h_in), dpi=300, facecolor="white")
            self._rysuj_zawartosc_na_figurze(fig_export)
            fig_export.savefig(sciezka, dpi=300, bbox_inches="tight", facecolor="white")
            QMessageBox.information(
                self, "Zapisano wykres",
                f"Zapisano wykres w skali 1:1 ({self.spn_width_cm.value()} cm x {self.spn_height_cm.value()} cm, 300 DPI):\n{sciezka}"
            )