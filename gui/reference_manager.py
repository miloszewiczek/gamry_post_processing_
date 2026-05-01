from PyQt5.QtWidgets import QDialog, QHBoxLayout, QPushButton, QComboBox, QVBoxLayout, QLabel, QInputDialog, QGridLayout, QFormLayout, QGroupBox, QTextEdit
from core.experiment_loader import ExperimentLoader
from gui_PtQt.config import references
from gui_PtQt.plotting_area import OCPPlot, PlottingCanvas
from functions.gui_functions import load_files, shorten_path
from pandas import DataFrame

class ReferenceManager(QDialog):
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
        self.references_types.addItems(list(references.get_electrode_types()) + ['<all>'])
        self.references_types.currentTextChanged.connect(self.update_combobox)

        # defined electrodes, a "child" of electrode type
        self.references_combobox = QComboBox()
        self.references_combobox.currentTextChanged.connect(self.update_reference_info)


        left_upper_layout.addRow(QLabel('Type'), self.references_types)
        left_upper_layout.addRow(QLabel('Electrode'),self.references_combobox)

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
        self.OCP_plotting_area.activate(event, self.select_btn, callback = self.add_entry)
        self.select_btn.setEnabled(False)

    def update_reference_info(self, event = None, electrode_name = None):

        if electrode_name is None:
            electrode_name = self.references_combobox.currentText()
        electrode_type = self.references_types.currentText()

        self.electrode_name.setText(electrode_name)
        self.electrode_type.setText(electrode_type)
        electrode_info = references.get_electrode_info(electrode_name)
        if electrode_info:
            fresh, days = references.get_newest_calibration(electrode_info)
            self.days_since_last_calibration.setText(str(days))
            short_path = shorten_path(str(fresh['filepath']))
            self.last_calibration_file.setText(short_path)
            self.last_calibration_offset.setText(str(fresh['calibration offset [V]']))
            self.last_notes.setText(fresh['notes'])
        else:
            self.days_since_last_calibration.setText('N/A')
            self.last_calibration_file.setText('N/A')
            self.last_calibration_offset.setText('N/A')
            self.last_notes.setText('N/A')


    def update_combobox(self, event = None):

        self.references_combobox.clear()
        if event is None:
            items_from_references = references.get_electrode_names(self.references_types.currentText())
            self.references_combobox.addItems(items_from_references + ["<new_electrode>"])
        else:
            electrode_labels = references.get_electrode_names(event)
            self.references_combobox.addItems(electrode_labels + ["<new_electrode>"])

            if event == '<all>':
                dataframe = references.get_all_electrode_data()
            else:
                dataframe = references.get_electrode_data(event)
            self.plot_calibration_potentials(dataframe = dataframe)


    def plot_calibration_potentials(self, dataframe = DataFrame):
        if dataframe is None:
            dataframe = references.get_all_electrode_data()
            print(dataframe)
            if dataframe is None:
                return
        self.reference_plotting_area.clear()
        dataframe.plot(ax = self.reference_plotting_area.axes, marker = 'o', markersize = '5')
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

    def add_entry(self):
        """Function to add entry into the reference_potentials.json file.
        It's based on the comboboxes in the left_layout Layout.
        Prompts the user if <all> or <new_electrode> options are selected."""

        electrode_type = self.references_types.currentText()
        electrode_id = self.references_combobox.currentText()
        if (electrode_id == "") or (electrode_id == '<new_electrode>'):
            electrode_id, done = QInputDialog.getText(self, 
                                              "Electrode label", 
                                              "No electrodes found. Define electrode label (e.g. \"AM\", \"6\" or other)")
            
            if done is False:
                return
        if (electrode_type == "") or (electrode_type == '<all>'):
            electrode_type, done = QInputDialog.getText(self, 
                                    "Electrode type", 
                                    "Specify the electrode type:\nAvailable:\nAgCl/Ag\nHg2Cl2/Hg\nHgO/Hg")
            if done is False:
                return
            
        
        time, offset = self.OCP_plotting_area.get_entry()

        # need to remember about this
        current_experiment = self.current_files[0]
        date = str(current_experiment.date_time)
        file_path = current_experiment.file_path
        
        # adding the data to .json file
        if offset:
            references.add_measurement(electrode_type = electrode_type,
                                       electrode_id = electrode_id,
                                      date =  date,
                                       file_path =  file_path,
                                        time = time,
                                         offset = offset)
            references.save()

            self.update_reference_info(electrode_name = electrode_id)
            self.update_combobox()