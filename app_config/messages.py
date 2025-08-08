#MESSAAGES FOR REQUIRING INPUT OF THE USER
input_messages = {

    #choronoamperometry.py
    'time_not_in_range' : 'Provided time not in range! Maximum time is {time_in_seconds} s.',
    'save_name': 'Please input the Excel output name'
}

#FOUND IN RESPECTIVE EXPERIMENT CLASSES (e.g. tafel_slope_new in LinearVoltammetry)
processing_messages = {
    'processing_data' : 'Saving data of {experiment_type} of cycle: {cycle}...',
    'processing_done' : 'Saving data of {experiment_type} of cycle: {cycle}... DONE!',
    'processing_data_fp_id_len' : 'Processing data of {file_path}, with id: {id} ({number_of_curves})',

    'line_method_potential' : 'Calculating difference at potential: {potential}',
    'tafel_slope_new' : ['Starting index point: {i_start}',
                         'Potential of starting point: {potential}',
                         'Potential of new point: {new_potential}',
                         'Index of new point: {i_end}',
                         'Next potential, including overlap: ({overlap}) - {new_potential_with_overlap}',
                         'Array is empty. Calculaton is finished. Check for errors']
}

#FOUND IN experiment_manager MODULE
manager_messages = {
    'retrieved_id' : 'Retrieved experiment with id: {id}',
    'retrieved_id_failed' : 'Failed to retrieve experiment with id: {id}',
    'no_experiments' : 'No experiments with provided id(s)',
    'chronology': ['Cycle number: {cycle_number}',
                   'Subcycle type: {experiment_name}',
                   'Total duration: {total_duration}'],
    'request_processing': 'No attribute: processed_data. Please run the process_data() method',
}

#GENERIC ERROR MESSAGES
error_messages = {
    'potential_out_of_range' : 'Potential used to calculate the current difference is out of experimental range'
    ''
}