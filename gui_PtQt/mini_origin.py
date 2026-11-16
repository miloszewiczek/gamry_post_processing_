import os
import re
import numpy as np
import pandas as pd

from PyQt5.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit, QFileDialog,
    QListWidget, QListWidgetItem, QGroupBox, QFormLayout, QMessageBox,
    QColorDialog, QSplitter, QScrollArea, QFrame, QGridLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.ticker import MultipleLocator


PALETA_DOMYSLNA = [
    "#1f77b4", "#d62728", "#2ca02c", "#ff7f0e",
    "#9467bd", "#000000", "#8c564b", "#e377c2", "#17becf"
]


def formatuj_tekst_osi(tekst):
    """
    Konwertuje zapis potęgowy (np. m^2, cm^-2, m2, cm2, s^-1) na indeksy górne
    z zachowaniem czcionki użytkownika (Arial / Times New Roman).
    """
    if not tekst:
        return ""
    t = str(tekst)
    # Zamiana typowych skrótów bez daszka w nawiasach/jednostkach
    mapa_jednostek = {
        "cm^-2": "cm⁻²",
        "cm-2": "cm⁻²",
        "/cm2": "/cm²",
        "cm^2": "cm²",
        "cm2": "cm²",
        "m^-2": "m⁻²",
        "m-2": "m⁻²",
        "/m2": "/m²",
        "m^2": "m²",
        "m2": "m²",
        "s^-1": "s⁻¹",
        "s-1": "s⁻¹",
        "^2": "²",
        "^3": "³",
        "^-1": "⁻¹",
        "^-2": "⁻²",
        "^-3": "⁻³",
    }
    for stary, nowy in mapa_jednostek.items():
        t = t.replace(stary, nowy)

    # Obsługa dowolnego zapisu ^{...} oraz _{...} przez \mathregular (zachowuje czcionkę Worda)
    t = re.sub(r"\^\{([^}]+)\}", r"$\\mathregular{^{\1}}$", t)
    t = re.sub(r"_\{([^}]+)\}", r"$\\mathregular{_{\1}}$", t)
    return t


def wyciagnij_xy_z_eksperymentu(exp):
    """Pobiera obrobione kolumny (X, Y) oraz opisy osi z obiektu Experiment."""
    xlabel, ylabel = "E_iR vs RHE [V]", "J_GEO [A/cm²]"

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


def _parsuj_liczbe(tekst):
    t = str(tekst).strip().replace(",", ".")
    if not t or t in ["-", ".", "+."]:
        return None
    try:
        val = float(t)
        return val if np.isfinite(val) else None
    except ValueError:
        return None


class MiniOriginDialog(QDialog):
    """Mini Origin z obsługą indeksów górnych (m², cm⁻²), skali osi, średniej z tłem i eksportu 1:1."""

    def __init__(self, selected_experiments=None, manager=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mini Origin – Stylizacja Wykresu, Jednostki (m²/cm⁻²), Skala Osi & Eksport LabPlot")
        self.resize(1420, 890)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)

        self.manager = manager
        self.serie = []
        self._blokuj_odswiezanie = True
        self._ostatnie_pole_osi = None

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
        self.domyslny_ylabel = "J_GEO [A/cm²]"

        for idx, exp in enumerate(lista_exp):
            x, y, xl, yl = wyciagnij_xy_z_eksperymentu(exp)
            if len(x) == 0:
                continue
            self.domyslny_xlabel = formatuj_tekst_osi(xl)
            self.domyslny_ylabel = formatuj_tekst_osi(yl)

            grupa_probki = getattr(exp, "user_tag", "") or "Próbka"
            nazwa = getattr(exp, "user_tag", "") or getattr(exp, "file_name", f"Krzywa_{idx+1}")
            if self.manager is not None:
                try:
                    sample = self.manager.find_sample(exp)
                    if sample and getattr(sample, "sample_name", ""):
                        base_sample = os.path.basename(sample.sample_name)
                        grupa_probki = getattr(sample, "user_tag", "") or base_sample
                        nazwa = f"{base_sample} - {getattr(exp, 'file_name', '')}"
                except Exception:
                    pass

            self.serie.append({
                "nazwa": str(nazwa),
                "grupa": str(grupa_probki),
                "x": x,
                "y": y,
                "kolor": PALETA_DOMYSLNA[idx % len(PALETA_DOMYSLNA)],
                "styl_linii": "-",
                "grubosc": 1.8,
                "widoczna": True,
                "ma_obszar": False,
                "y_std": None,
                "y_sem": None,
                "y_min": None,
                "y_max": None
            })

    def _zbuduj_interfejs(self):
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # ================= LEWY PANEL USTAWIEŃ (PRZEWIJANY) =================
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setMinimumWidth(440)
        left_scroll.setMaximumWidth(485)
        left_scroll.setFrameShape(QFrame.NoFrame)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_scroll.setWidget(left_widget)

        # 1. Lista krzywych
        grp_krzywe = QGroupBox("1. Wybrane krzywe (zaznacz/odznacz widoczność)")
        v_krzywe = QVBoxLayout(grp_krzywe)

        self.lista_widget = QListWidget()
        self.lista_widget.setMinimumHeight(105)
        self.lista_widget.currentRowChanged.connect(self.wybrano_krzywa)
        self.lista_widget.itemChanged.connect(self.zmieniono_widocznosc_krzywej)
        v_krzywe.addWidget(self.lista_widget)

        h_sel_btns = QHBoxLayout()
        btn_sel_all = QPushButton("Zaznacz wszystkie")
        btn_sel_all.clicked.connect(lambda: self.ustaw_widocznosc_wszystkich(True))
        btn_unsel_all = QPushButton("Odznacz wszystkie")
        btn_unsel_all.clicked.connect(lambda: self.ustaw_widocznosc_wszystkich(False))
        btn_del_cur = QPushButton("Usuń wybraną")
        btn_del_cur.setStyleSheet("color: #DC2626;")
        btn_del_cur.clicked.connect(self.usun_wybrana_krzywa)
        h_sel_btns.addWidget(btn_sel_all)
        h_sel_btns.addWidget(btn_unsel_all)
        h_sel_btns.addWidget(btn_del_cur)
        v_krzywe.addLayout(h_sel_btns)

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

        btn_kolor = QPushButton("Zmień kolor zaznaczonej krzywej / tła...")
        btn_kolor.setStyleSheet("background-color: #2563EB; color: white; font-weight: bold; padding: 5px;")
        btn_kolor.clicked.connect(self.zmien_kolor)
        f_krzywa.addRow(btn_kolor)

        v_krzywe.addLayout(f_krzywa)
        left_layout.addWidget(grp_krzywe)

        # 2. Średnia z wyników i cieniowany obszar tła (fill_between)
        grp_mean = QGroupBox("2. Średnia i cieniowany obszar błędu (lżejsze tło)")
        v_mean = QVBoxLayout(grp_mean)

        btn_add_mean = QPushButton("Dodaj średnią + obszar tła z zaznaczonych krzywych")
        btn_add_mean.setStyleSheet("background-color: #0D9488; color: white; font-weight: bold; padding: 6px;")
        btn_add_mean.clicked.connect(self.utworz_srednia_z_zaznaczonych)
        v_mean.addWidget(btn_add_mean)

        btn_auto_group_mean = QPushButton("Uśrednij osobno każdą próbkę (wg folderu / tagu)")
        btn_auto_group_mean.setStyleSheet("background-color: #0284C7; color: white; font-weight: bold; padding: 5px;")
        btn_auto_group_mean.clicked.connect(self.utworz_srednie_wg_probek)
        v_mean.addWidget(btn_auto_group_mean)

        f_mean = QFormLayout()
        self.cmb_obszar_typ = QComboBox()
        self.cmb_obszar_typ.addItems([
            "Włączony: Odchylenie standardowe (±SD)",
            "Włączony: Zakres Min–Max (obwiednia)",
            "Włączony: Błąd standardowy (±SE)",
            "Wyłączony (Tylko linia średniej bez tła)"
        ])
        self.cmb_obszar_typ.currentIndexChanged.connect(self.odswiez_wykres)
        f_mean.addRow("Rodzaj tła:", self.cmb_obszar_typ)

        self.spn_alpha = QDoubleSpinBox()
        self.spn_alpha.setRange(0.05, 0.85)
        self.spn_alpha.setSingleStep(0.05)
        self.spn_alpha.setValue(0.25)
        self.spn_alpha.valueChanged.connect(self.odswiez_wykres)
        f_mean.addRow("Przezroczystość tła (Alpha):", self.spn_alpha)

        v_mean.addLayout(f_mean)
        left_layout.addWidget(grp_mean)

        # 3. Czcionki (pt) i rozmiar pod Worda (zsynchronizowany z CDL)
        grp_font = QGroupBox("3. Czcionka (pt), Styl i Rozmiar Warstwy (identyczny z CDL)")
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

        # 4. Zakres osi X i Y oraz krok podziałki
        grp_scale = QGroupBox("4. Zakres osi X i Y oraz krok podziałki (puste = Auto)")
        v_scale = QVBoxLayout(grp_scale)

        grid_scale = QGridLayout()
        grid_scale.addWidget(QLabel("<b>Oś</b>"), 0, 0)
        grid_scale.addWidget(QLabel("<b>Od (Min)</b>"), 0, 1)
        grid_scale.addWidget(QLabel("<b>Do (Max)</b>"), 0, 2)
        grid_scale.addWidget(QLabel("<b>Krok (co ile)</b>"), 0, 3)

        self.inp_xmin = QLineEdit()
        self.inp_xmin.setPlaceholderText("Auto")
        self.inp_xmax = QLineEdit()
        self.inp_xmax.setPlaceholderText("Auto")
        self.inp_xstep = QLineEdit()
        self.inp_xstep.setPlaceholderText("np. 0.5")

        self.inp_ymin = QLineEdit()
        self.inp_ymin.setPlaceholderText("Auto")
        self.inp_ymax = QLineEdit()
        self.inp_ymax.setPlaceholderText("Auto")
        self.inp_ystep = QLineEdit()
        self.inp_ystep.setPlaceholderText("np. 0.2")

        for w in [self.inp_xmin, self.inp_xmax, self.inp_xstep, self.inp_ymin, self.inp_ymax, self.inp_ystep]:
            w.textChanged.connect(self.odswiez_wykres)

        grid_scale.addWidget(QLabel("<b>Oś X:</b>"), 1, 0)
        grid_scale.addWidget(self.inp_xmin, 1, 1)
        grid_scale.addWidget(self.inp_xmax, 1, 2)
        grid_scale.addWidget(self.inp_xstep, 1, 3)

        grid_scale.addWidget(QLabel("<b>Oś Y:</b>"), 2, 0)
        grid_scale.addWidget(self.inp_ymin, 2, 1)
        grid_scale.addWidget(self.inp_ymax, 2, 2)
        grid_scale.addWidget(self.inp_ystep, 2, 3)

        v_scale.addLayout(grid_scale)

        h_scale_btns = QHBoxLayout()
        btn_fill_bounds = QPushButton("Pobierz obecny zakres")
        btn_fill_bounds.clicked.connect(self.pobierz_obecny_zakres_osi)
        btn_reset_bounds = QPushButton("Resetuj skalę do Auto")
        btn_reset_bounds.clicked.connect(self.resetuj_zakres_osi)
        h_scale_btns.addWidget(btn_fill_bounds)
        h_scale_btns.addWidget(btn_reset_bounds)
        v_scale.addLayout(h_scale_btns)

        left_layout.addWidget(grp_scale)

        # 5. Opisy osi, indeksy górne (m², cm⁻²) i wygląd
        grp_axes = QGroupBox("5. Podpisy osi, indeksy górne (m², cm⁻²) i jednostki")
        v_axes = QVBoxLayout(grp_axes)
        f_axes = QFormLayout()

        self.cmb_y_mult = QComboBox()
        self.cmb_y_mult.addItems(["1x (Oryginalna jednostka)", "1000x (Przelicz A/cm² -> mA/cm²)"])
        self.cmb_y_mult.currentIndexChanged.connect(self.zmieniono_mnoznik_y)
        f_axes.addRow("Skala osi Y:", self.cmb_y_mult)

        self.inp_title = QLineEdit("")
        self.inp_title.textChanged.connect(self.odswiez_wykres)
        f_axes.addRow("Tytuł wykresu:", self.inp_title)

        self.inp_xlabel = QLineEdit(getattr(self, "domyslny_xlabel", "E_iR vs RHE [V]"))
        self.inp_xlabel.textChanged.connect(self.odswiez_wykres)
        self.inp_xlabel. selectionChanged.connect(lambda: setattr(self, "_ostatnie_pole_osi", self.inp_xlabel))
        self.inp_xlabel.textEdited.connect(lambda _: setattr(self, "_ostatnie_pole_osi", self.inp_xlabel))
        f_axes.addRow("Oś X:", self.inp_xlabel)

        self.inp_ylabel = QLineEdit(getattr(self, "domyslny_ylabel", "J_GEO [A/cm²]"))
        self.inp_ylabel.textChanged.connect(self.odswiez_wykres)
        self.inp_ylabel.selectionChanged.connect(lambda: setattr(self, "_ostatnie_pole_osi", self.inp_ylabel))
        self.inp_ylabel.textEdited.connect(lambda _: setattr(self, "_ostatnie_pole_osi", self.inp_ylabel))
        self. _ostatnie_pole_osi = self.inp_ylabel
        f_axes.addRow("Oś Y:", self.inp_ylabel)

        v_axes.addLayout(f_axes)

        # Pasek szybkiego wstawiania indeksów górnych i jednostek
        lbl_hint = QLabel("<small>Kliknij w pole Oś X lub Oś Y, aby wstawić indeks górny (lub wpisz np. m^2, cm^-2):</small>")
        v_axes.addWidget(lbl_hint)

        h_sup = QHBoxLayout()
        for symbol, tekst_wstaw in [
            ("x²", "²"),
            ("x⁻²", "⁻²"),
            ("x⁻¹", "⁻¹"),
            ("m²", "m²"),
            ("cm²", "cm²"),
            ("cm⁻²", "cm⁻²"),
            ("mV s⁻¹", "mV s⁻¹"),
        ]:
            b = QPushButton(symbol)
            b.setMaximumWidth(58)
            b.clicked.connect(lambda _, t=tekst_wstaw: self.wstaw_symbol_do_opisu(t))
            h_sup.addWidget(b)
        v_axes.addLayout(h_sup)

        f_grid_leg = QFormLayout()
        self.cmb_grid = QComboBox()
        self.cmb_grid.addItems(["Włączona (Przerywana)", "Włączona (Ciągła)", "Wyłączona"])
        self.cmb_grid.currentIndexChanged.connect(self.odswiez_wykres)
        f_grid_leg.addRow("Siatka (Grid):", self.cmb_grid)

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
        f_grid_leg.addRow("Legenda:", self.cmb_legend_loc)
        v_axes.addLayout(f_grid_leg)

        left_layout.addWidget(grp_axes)

        # 6. Przyciski zapisu
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

    def wstaw_symbol_do_opisu(self, tekst_do_wstawienia):
        pole = self._ostatnie_pole_osi if self._ostatnie_pole_osi is not None else self.inp_ylabel
        pole.insert(tekst_do_wstawienia)
        pole.setFocus()
        self.odswiez_wykres()

    # -------------------------------------------------------------------------
    # OBSŁUGA ZAKRESÓW OSI X / Y
    # -------------------------------------------------------------------------
    def pobierz_obecny_zakres_osi(self):
        if self.ax is None:
            return
        self._blokuj_odswiezanie = True
        x0, x1 = self.ax.get_xlim()
        y0, y1 = self.ax.get_ylim()
        self.inp_xmin.setText(f"{x0:.4g}")
        self.inp_xmax.setText(f"{x1:.4g}")
        self.inp_ymin.setText(f"{y0:.4g}")
        self.inp_ymax.setText(f"{y1:.4g}")
        self._blokuj_odswiezanie = False
        self.odswiez_wykres()

    def resetuj_zakres_osi(self):
        self._blokuj_odswiezanie = True
        for w in [self.inp_xmin, self.inp_xmax, self.inp_xstep, self.inp_ymin, self.inp_ymax, self.inp_ystep]:
            w.clear()
        self._blokuj_odswiezanie = False
        self.odswiez_wykres()

    # -------------------------------------------------------------------------
    # OBLICZANIE ŚREDNIEJ I CIENIOWANEGO OBSZARU TŁA (FILL_BETWEEN)
    # -------------------------------------------------------------------------
    def _oblicz_srednia_dla_listy_serii(self, wybrane_serie, nazwa_nowej, kolor):
        poprawne = [s for s in wybrane_serie if len(s["x"]) >= 2]
        if not poprawne:
            return None

        xs_sorted, ys_sorted = [], []
        for s in poprawne:
            x_arr = np.asarray(s["x"], dtype=float)
            y_arr = np.asarray(s["y"], dtype=float)
            order = np.argsort(x_arr)
            xs_sorted.append(x_arr[order])
            ys_sorted.append(y_arr[order])

        x_min = max(np.min(x) for x in xs_sorted)
        x_max = min(np.max(x) for x in xs_sorted)
        if x_min >= x_max:
            x_min = min(np.min(x) for x in xs_sorted)
            x_max = max(np.max(x) for x in xs_sorted)

        n_pts = max(len(x) for x in xs_sorted)
        x_common = np.linspace(x_min, x_max, n_pts)

        y_matrix = np.vstack([np.interp(x_common, x, y) for x, y in zip(xs_sorted, ys_sorted)])
        y_mean = np.nanmean(y_matrix, axis=0)
        ddof = 1 if len(poprawne) > 1 else 0
        y_std = np.nanstd(y_matrix, axis=0, ddof=ddof)
        y_sem = y_std / np.sqrt(len(poprawne))
        y_min = np.nanmin(y_matrix, axis=0)
        y_max = np.nanmax(y_matrix, axis=0)

        return {
            "nazwa": nazwa_nowej,
            "grupa": "Średnia",
            "x": x_common,
            "y": y_mean,
            "kolor": kolor,
            "styl_linii": "-",
            "grubosc": max(2.2, self.spn_line_width.value()),
            "widoczna": True,
            "ma_obszar": True,
            "y_std": y_std,
            "y_sem": y_sem,
            "y_min": y_min,
            "y_max": y_max
        }

    def utworz_srednia_z_zaznaczonych(self):
        widoczne = [s for s in self.serie if s.get("widoczna", True) and not s.get("ma_obszar", False)]
        if len(widoczne) < 2:
            QMessageBox.information(
                self, "Zbyt mało krzywych",
                "Zaznacz na liście co najmniej 2 pojedyncze krzywe, aby wyliczyć z nich średnią i obszar tła."
            )
            return

        wspolna_grupa = widoczne[0].get("grupa", "Średnia")
        nazwa_sredniej = f"{wspolna_grupa} (Średnia n={len(widoczne)})"
        kolor = widoczne[0]["kolor"]

        nowa_seria = self._oblicz_srednia_dla_listy_serii(widoczne, nazwa_sredniej, kolor)
        if nowa_seria is None:
            return

        for s in widoczne:
            s["widoczna"] = False

        self.serie.append(nowa_seria)
        self._odswiez_liste_widget()
        self.lista_widget.setCurrentRow(len(self.serie) - 1)
        self.odswiez_wykres()

    def utworz_srednie_wg_probek(self):
        surowe = [s for s in self.serie if not s.get("ma_obszar", False)]
        if not surowe:
            return

        grupy = {}
        for s in surowe:
            klucz = s.get("grupa", "Próbka")
            grupy.setdefault(klucz, []).append(s)

        dodano = 0
        for idx_g, (nazwa_grupy, lista_s) in enumerate(grupy.items()):
            if len(lista_s) < 1:
                continue
            kolor = PALETA_DOMYSLNA[idx_g % len(PALETA_DOMYSLNA)]
            nowa = self._oblicz_srednia_dla_listy_serii(
                lista_s, f"{nazwa_grupy} (Średnia n={len(lista_s)})", kolor
            )
            if nowa is not None:
                for s in lista_s:
                    s["widoczna"] = False
                self.serie.append(nowa)
                dodano += 1

        if dodano > 0:
            self._odswiez_liste_widget()
            self.lista_widget.setCurrentRow(len(self.serie) - 1)
            self.odswiez_wykres()

    # -------------------------------------------------------------------------
    # ZARZĄDZANIE LISTĄ KRZYWYCH
    # -------------------------------------------------------------------------
    def ustaw_widocznosc_wszystkich(self, stan):
        for s in self.serie:
            s["widoczna"] = bool(stan)
        self._odswiez_liste_widget()
        self.odswiez_wykres()

    def usun_wybrana_krzywa(self):
        row = self.lista_widget.currentRow()
        if 0 <= row < len(self.serie):
            del self.serie[row]
            self._odswiez_liste_widget()
            if self.serie:
                self.lista_widget.setCurrentRow(min(row, len(self.serie) - 1))
            self.odswiez_wykres()

    def _odswiez_liste_widget(self):
        self.lista_widget.blockSignals(True)
        self.lista_widget.clear()
        for s in self.serie:
            etykieta = f"[ŚREDNIA + TŁO] {s['nazwa']}" if s.get("ma_obszar", False) else s["nazwa"]
            item = QListWidgetItem(etykieta)
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
            etykieta = f"[ŚREDNIA + TŁO] {nowa_nazwa}" if self.serie[row].get("ma_obszar", False) else nowa_nazwa
            item.setText(etykieta)
        self.lista_widget.blockSignals(False)

        self.odswiez_wykres()

    def zmien_kolor(self):
        row = self.lista_widget.currentRow()
        if row < 0 or row >= len(self.serie):
            return
        kolor = QColorDialog.getColor(QColor(self.serie[row]["kolor"]), self, "Wybierz kolor krzywej i tła")
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

    # -------------------------------------------------------------------------
    # RYSOWANIE WYKRESU, SKALI OSI ORAZ CIENIOWANEGO TŁA
    # -------------------------------------------------------------------------
    def _pobierz_granice_obszaru(self, s, mnoznik_y):
        typ = self.cmb_obszar_typ.currentIndex()
        if typ == 3 or not s.get("ma_obszar", False):
            return None, None

        y_mean = s["y"] * mnoznik_y
        if typ == 0 and s.get("y_std") is not None:
            err = s["y_std"] * mnoznik_y
            return y_mean - err, y_mean + err
        elif typ == 1 and s.get("y_min") is not None and s.get("y_max") is not None:
            return s["y_min"] * mnoznik_y, s["y_max"] * mnoznik_y
        elif typ == 2 and s.get("y_sem") is not None:
            err = s["y_sem"] * mnoznik_y
            return y_mean - err, y_mean + err
        return None, None

    def _rysuj_zawartosc_na_figurze(self, fig):
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
        alpha_tla = self.spn_alpha.value()

        widoczne_serie = [s for s in self.serie if s.get("widoczna", True)]
        for s in widoczne_serie:
            y_dol, y_gora = self._pobierz_granice_obszaru(s, mnoznik_y)
            if y_dol is not None and y_gora is not None:
                ax.fill_between(
                    s["x"], y_dol, y_gora,
                    color=s["kolor"],
                    alpha=alpha_tla,
                    linewidth=0
                )

            ax.plot(
                s["x"], s["y"] * mnoznik_y,
                color=s["kolor"],
                linestyle=s["styl_linii"],
                linewidth=s["grubosc"],
                label=s["nazwa"]
            )

        xmin = _parsuj_liczbe(self.inp_xmin.text())
        xmax = _parsuj_liczbe(self.inp_xmax.text())
        xstep = _parsuj_liczbe(self.inp_xstep.text())

        ymin = _parsuj_liczbe(self.inp_ymin.text())
        ymax = _parsuj_liczbe(self.inp_ymax.text())
        ystep = _parsuj_liczbe(self.inp_ystep.text())

        if xmin is not None or xmax is not None:
            ax.set_xlim(left=xmin, right=xmax)
        if ymin is not None or ymax is not None:
            ax.set_ylim(bottom=ymin, top=ymax)

        if xstep is not None and xstep > 0:
            x0, x1 = ax.get_xlim()
            if 0 < abs(x1 - x0) / xstep <= 150:
                if xmin is not None and xmax is not None and xmin < xmax:
                    ax.set_xticks(np.arange(xmin, xmax + xstep * 1e-5, xstep))
                    ax.set_xlim(xmin, xmax)
                else:
                    ax.xaxis.set_major_locator(MultipleLocator(xstep))

        if ystep is not None and ystep > 0:
            y0, y1 = ax.get_ylim()
            if 0 < abs(y1 - y0) / ystep <= 150:
                if ymin is not None and ymax is not None and ymin < ymax:
                    ax.set_yticks(np.arange(ymin, ymax + ystep * 1e-5, ystep))
                    ax.set_ylim(ymin, ymax)
                else:
                    ax.yaxis.set_major_locator(MultipleLocator(ystep))

        if self.inp_title.text().strip():
            ax.set_title(
                formatuj_tekst_osi(self.inp_title.text()),
                fontname=family, fontsize=legend_pt + 1,
                fontweight=weight, fontstyle=fstyle, pad=8
            )

        ax.set_xlabel(formatuj_tekst_osi(self.inp_xlabel.text()), fontname=family, fontsize=label_pt, fontweight=weight, fontstyle=fstyle)
        ax.set_ylabel(formatuj_tekst_osi(self.inp_ylabel.text()), fontname=family, fontsize=label_pt, fontweight=weight, fontstyle=fstyle)

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

        fig.tight_layout(pad=0.6)
        return ax

    def odswiez_wykres(self):
        if self._blokuj_odswiezanie:
            return

        w_in = self.spn_width_cm.value() / 2.54
        h_in = self.spn_height_cm.value() / 2.54

        base_dpi = getattr(self.fig, "_original_dpi", 100.0)
        target_w = int(round(w_in * base_dpi))
        target_h = int(round(h_in * base_dpi))

        if self.canvas.width() != target_w or self.canvas.height() != target_h:
            self.canvas.setFixedSize(target_w, target_h)

        self.ax = self._rysuj_zawartosc_na_figurze(self.fig)
        self.canvas.draw()
        self.canvas.update()

    # -------------------------------------------------------------------------
    # EKSPORT DO EXCELA / LABPLOT ORAZ ZAPIS OBRAZKA 300 DPI
    # -------------------------------------------------------------------------
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
            n = len(s["x"])
            x_pad = np.full(max_len, np.nan)
            y_pad = np.full(max_len, np.nan)
            x_pad[:n] = s["x"]
            y_pad[:n] = s["y"] * mnoznik_y
            kolumny[f"X_{nazwa}"] = x_pad
            kolumny[f"Y_{nazwa}"] = y_pad

            if s.get("ma_obszar", False) and s.get("y_std") is not None:
                sd_pad = np.full(max_len, np.nan)
                sd_pad[:n] = s["y_std"] * mnoznik_y
                kolumny[f"Y_SD_{nazwa}"] = sd_pad

                y_dol, y_gora = self._pobierz_granice_obszaru(s, mnoznik_y)
                if y_dol is not None and y_gora is not None:
                    dol_pad = np.full(max_len, np.nan)
                    gora_pad = np.full(max_len, np.nan)
                    dol_pad[:n] = y_dol
                    gora_pad[:n] = y_gora
                    kolumny[f"Y_Dolny_Obszar_{nazwa}"] = dol_pad
                    kolumny[f"Y_Gorny_Obszar_{nazwa}"] = gora_pad

        df_out = pd.DataFrame(kolumny)
        if sciezka.lower().endswith(".csv"):
            df_out.to_csv(sciezka, sep="\t", index=False)
        else:
            with pd.ExcelWriter(sciezka, engine="xlsxwriter") as writer:
                df_out.to_excel(writer, sheet_name="Dane_XY_LabPlot", index=False)

        QMessageBox.information(
            self, "Zapisano dane XY",
            f"Zapisano kolumny X i Y (wraz z granicami obszaru błędu) pod LabPlot:\n{sciezka}"
        )

    def zapisz_obrazek(self):
        sciezka, _ = QFileDialog.getSaveFileName(
            self, "Zapisz wykres w skali Worda (300 DPI)",
            "Wykres_LSV_Word_300DPI.png", "Obraz PNG 300 DPI (*.png);;Dokument PDF (*.pdf)"
        )
        if sciezka:
            w_in = self.spn_width_cm.value() / 2.54
            h_in = self.spn_height_cm.value() / 2.54
            fig_export = Figure(figsize=(w_in, h_in), dpi=300, facecolor="white")
            self._rysuj_zawartosc_na_figurze(fig_export)
            fig_export.savefig(sciezka, dpi=300, bbox_inches="tight", facecolor="white")
            QMessageBox.information(
                self, "Zapisano wykres",
                f"Zapisano wykres w skali 1:1 ({self.spn_width_cm.value()} cm x {self.spn_height_cm.value()} cm, 300 DPI):\n{sciezka}"
            )