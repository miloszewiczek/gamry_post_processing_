from PyQt5.QtWidgets import QDialog, QDoubleSpinBox, QPushButton, QHBoxLayout, QVBoxLayout, QDialog, QComboBox, QLabel

class area_dialog_box(QDialog):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        label = QLabel('Area type')
        
        layout.addWidget(label)
        area_type_combo = QComboBox()
        area_type_combo.addItems(['Circle', 'Rectangle', 'Square'])
        area_type_combo.setCurrentIndex(0)
        area_type_combo.currentTextChanged.connect(self.update)
        layout.addWidget(area_type_combo)
        self.setLayout(layout)

    def update(self, item_text):
        print(item_text)
        if item_text == 'Circle':
            selfQLabel('DUPAAAA')
        else:
            return
        
        
        
