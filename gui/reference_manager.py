from PyQt5.QtWidgets import QDialog, QHBoxLayout, QPushButton, QComboBox, QVBoxLayout, QLabel, QInputDialog, QGridLayout, QFormLayout, QGroupBox, QTextEdit
from PyQt5.QtGui import QIcon
from core.experiment_loader import ExperimentLoader
from gui_PtQt.config import references, icon_path
from gui_PtQt.plotting_area import OCPPlot, PlottingCanvas
from functions.gui_functions import load_files, shorten_path
from pandas import DataFrame


class ReferenceManagerWindow(QDialog):
    def __init__(self):
        super().__init__()

        master_layout = QVBoxLayout()
        layout = QHBoxLayout()
        self.setLayout(master_layout)

        left_layout = QVBoxLayout()
        left_upper_groupbox = QGroupBox('1. Electrode selection')
        left_upper_layout = QFormLayout()
    
        left_upper_groupbox.setLayout(left_upper_layout)
        left_layout.addWidget(left_upper_groupbox)

        information_groupbox = QGroupBox('2. Electrode information')
        information_layout = QFormLayout()
        self.electrode_name = QLabel()
        self.electrode_type = QLabel()
        self.days_since_last_calibration = QLabel()
        self.last_calibration_offset = QLabel()
        self.last_notes = QTextEdit()
        self.last_calibration_file = QLabel()

        self.information_dict = {QLabel('Label: '): self.electrode_name,
                            QLabel('Type: '): self.electrode_type,
                            QLabel('Last file: '): self.last_calibration_file,
                            QLabel('Last calibration: '): self.days_since_last_calibration,
                            QLabel('Last offset [V]: '): self.last_calibration_offset,
                            QLabel('Notes: '): self.last_notes}
        for label, widget in self.information_dict.items():
            information_layout.addRow(label, widget)
        information_groupbox.setLayout(information_layout)
        left_layout.addWidget(information_groupbox)

        

        left_down_groupbox = QGroupBox('3. Entry points')
        left_down_layout = QVBoxLayout()
        left_down_groupbox.setLayout(left_down_layout)

        load_calibration_OCP = QPushButton('Load OCP file')
        left_down_layout.addWidget(load_calibration_OCP)
        load_calibration_OCP.clicked.connect(self.load_files_and_process)

        
        # electrode types such as AgCl/Ag
        self.references_types = QComboBox()
        self.references_types.addItems(list(references.electrodes.keys()) + ['<all>'])
        self.references_types.currentTextChanged.connect(self.update_combobox)

        # defined electrodes, a "child" of electrode type
        self.references_combobox = QComboBox()
        self.references_combobox.currentTextChanged.connect(self.update_reference_info)


        add_new_electrode_button = QPushButton('Add')
        add_new_electrode_button.setIcon(QIcon(icon_path + 'plus'))
        add_new_electrode_button.clicked.connect(self.create_new_reference_electrode)

        row_layout = QHBoxLayout()
        row_layout.addWidget(self.references_combobox, stretch = 1)
        row_layout.addWidget(add_new_electrode_button)

        left_upper_layout.addRow(QLabel('Type'), self.references_types)
        left_upper_layout.addRow(QLabel('Electrode'), row_layout)

        left_layout.addLayout(left_upper_layout)
        left_layout.addLayout(left_down_layout)

        

        entry_point_groupbox = QGroupBox('3. Adding entries')
        ocp_layout = QVBoxLayout()

        figures_layout = QHBoxLayout()
        self.current_point_label = QLabel("Select a point") 
        self.OCP_plotting_area = OCPPlot((5,5), 100, self.current_point_label)
        self.load_btn = QPushButton('Load file')
        self.select_btn = QPushButton('Select')
        self.select_btn.clicked.connect(self.select_point)
        self.load_btn.clicked.connect(self.load_files_and_process)

        entry_point_groupbox.setLayout(ocp_layout)
        ocp_layout.addWidget(self.current_point_label)
        ocp_layout.addWidget(self.load_btn)
        ocp_layout.addWidget(self.select_btn)
        ocp_layout.addWidget(self.OCP_plotting_area)


        self.reference_plotting_area = PlottingCanvas()
        figures_layout.addWidget(entry_point_groupbox)
        figures_layout.addWidget(self.reference_plotting_area)

        layout.addLayout(left_layout)
        layout.addLayout(figures_layout)

        button_layout = QHBoxLayout()
        ok_button = QPushButton('OK')
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton('Cancel')

        master_layout.addLayout(layout)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        master_layout.addLayout(button_layout)


        # initializing
        self.update_combobox(None)
        self.plot_calibration_potentials(None)

    def get_data(self):
        return self.electrode_type.text(), float(self.last_calibration_offset.text())

    def select_point(self, event):
        self.OCP_plotting_area.activate(event, self.select_btn, callback = self.add_measurement)
        self.select_btn.setEnabled(False)

    def update_reference_info(self, event = None, electrode_name = None):

        if electrode_name is None:
            electrode_name = self.references_combobox.currentText()
        electrode_type = self.references_types.currentText()

        self.electrode_name.setText(electrode_name)
        self.electrode_type.setText(electrode_type)
        electrode = references.get_electrode(label = electrode_name)
        if electrode:
            electrode_info = electrode[0].get_info()

            if electrode_info:
                self.days_since_last_calibration.setText(str(electrode_info['last_calibration_date']))
                short_path = shorten_path(str(electrode_info['filepath']))
                self.last_calibration_file.setText(short_path)
                self.last_calibration_offset.setText(str(electrode_info['calibration offset [V]']))
                self.last_notes.setText(electrode_info['notes'])
                return
            self.set_blank_info()
        else:
            self.set_blank_info()

    def set_blank_info(self):
        self.days_since_last_calibration.setText('N/A')
        self.last_calibration_file.setText('N/A')
        self.last_calibration_offset.setText('N/A')
        self.last_notes.setText('N/A')


    def update_combobox(self, event = None):

        if event == '<all>':
            current_electrodes = references.get_electrode(all = True, group = False)
        else:
            current_electrodes = references.get_electrode(electrode_type = self.references_types.currentText())
        if current_electrodes:

            current_electrodes_labels = [electrode.label for electrode in current_electrodes]
            self.references_combobox.clear()
            self.references_combobox.addItems(current_electrodes_labels)
            dataframe = references.get_electrodes_data(current_electrodes)
            self.plot_calibration_potentials(dataframe = dataframe)
            self.references_combobox.setEnabled(True)
            return
        
        self.references_combobox.setEnabled(False)
        self.reference_plotting_area.axes.clear()
        self.reference_plotting_area.draw_idle()
        return


    def plot_calibration_potentials(self, dataframe = DataFrame):
        if dataframe is None:
            electrodes = references.get_electrode(all = True, group = False)
            electrodes_df = references.get_electrodes_data(electrodes)
            if electrodes_df is None:
                return
        else:
            electrodes_df = dataframe
        self.reference_plotting_area.clear()
        electrodes_df.plot(ax = self.reference_plotting_area.axes, marker = 'o', markersize = '5')
        self.reference_plotting_area.draw_idle()

            
    def load_files_and_process(self, event):
        "Simple function that creates the OCP data to view"

        loader = ExperimentLoader()
        files = load_files()
        self.current_files = [loader.create_experiment(file) for file in files]
        for file in self.current_files:
            file.process_data()
        self.OCP_plotting_area.plot_experiments(self.current_files)

    def load(self):
        return references.get_electrodes()

    def create_new_reference_electrode(self):

        current_type = self.references_types.currentText()
        electrode_label, done = QInputDialog.getText(self, 
                                    "New reference electrode", 
                                    f"You are trying to create a new {current_type} electrode.\n Choose name.")

        if done:
            new_electrode = references.create_electrode(electrode_type = current_type, 
                                                        label = electrode_label)
        self.update_combobox()
        self.references_combobox.setCurrentText(new_electrode.label)

    def add_measurement(self):
        current_electrode = references.get_electrode(label = self.references_combobox.currentText())[0]
        
        time, offset = self.OCP_plotting_area.get_entry()
        
        # need to remember about this
        if offset:
            current_experiment = self.current_files[0]
            date = str(current_experiment.date_time)
            file_path = current_experiment.file_path

            current_electrode.add_data(date_time = date, 
                                        file_path = file_path,
                                        time_at_offset = time,
                                        calibration_offset = offset,
                                        notes = None) # for future use
            
            self.update_combobox()
            self.update_reference_info(electrode_name = current_electrode.label)
            self.references_combobox.setCurrentText(current_electrode.label)
