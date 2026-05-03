from PyQt5.QtWidgets import QDoubleSpinBox, QDialog, QSpinBox, QComboBox, QLineEdit, QCheckBox
from PyQt5.QtCore import QSettings
import json

class SimpleDoubleSpinBox(QDoubleSpinBox):
    def __init__(self, value, range:tuple = None):
        super().__init__()
        self.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        self.setDecimals(3)
        self.setValue(value)
        if range:
            self.setRange(range[0], range[1])


class BaseDataDialog(QDialog):
    def __init__(self, parent=None, settings_key = None):
        super().__init__(parent)
        self.fields = {}
        # Klucz, pod którym okno będzie pamiętać swoje ustawienia w QSettings
        self.settings_key = settings_key

    def get_data(self):
        """Automatycznie zbiera dane z widgetów zarejestrowanych w self.fields."""
        data = {}
        for key, widget in self.fields.items():
            if isinstance(widget, QDoubleSpinBox) or isinstance(widget, QSpinBox):
                data[key] = widget.value()
            elif isinstance(widget, QComboBox):
                # Zwracamy currentData (jeśli przechowujesz tam np. tuple z potencjałami)
                # Jeśli danych nie ma, fallback do currentText()
                val = widget.currentData()
                data[key] = val if val is not None else widget.currentText()
            elif isinstance(widget, QCheckBox):
                data[key] = widget.isChecked()
            elif isinstance(widget, QLineEdit):
                data[key] = widget.text()

            else:
                # Opcjonalnie: obsługa własnych atrybutów, jeśli widget ma metodę 'get_value'
                if hasattr(widget, 'get_value'):
                    data[key] = widget.get_value()
        return data

    def set_data(self, data):
        """Automatycznie rozsyła dane do odpowiednich widgetów."""
        if not data:
            return

        self.blockSignals(True)
        for key, value in data.items():
            widget = self.fields.get(key)
            if not widget:
                continue

            if isinstance(widget, (QDoubleSpinBox, QSpinBox)):
                widget.setValue(float(value))
            elif isinstance(widget, QCheckBox):
                widget.setChecked(bool(value))
            elif isinstance(widget, QLineEdit):
                widget.setText(str(value))
            elif isinstance(widget, QComboBox):
                # Próbujemy ustawić po tekście (najbezpieczniejsze dla profili JSON)
                index = widget.findText(str(value))
                if index >= 0:
                    widget.setCurrentIndex(index)
                # Jeśli value to int (index), ustawiamy po indeksie
                elif isinstance(value, int):
                    widget.setCurrentIndex(value)
        self.blockSignals(False)


    def load_from_settings(self):
        """Ładuje ostatnie wartości z QSettings."""
        if not self.settings_key:
            return
            
        settings = QSettings()
        raw_data = settings.value(f"cache/{self.settings_key}")
        if raw_data:
            try:
                self.set_data(json.loads(raw_data))
            except Exception as e:
                print(f"Błąd ładowania cache: {e}")

    def save_to_settings(self):
        """Zapisuje aktualne wartości do QSettings."""
        if not self.settings_key:
            return
            
        settings = QSettings()
        data = self.get_data()
        settings.setValue(f"cache/{self.settings_key}", json.dumps(data))