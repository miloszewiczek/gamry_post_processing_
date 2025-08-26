from experiments import *
import tabulate
import re
from typing import Literal

class ExperimentManager():
    def __init__(self):
        self.atr = None
        self.filtered = None
        self.list_of_experiments = []

            
    def combine_experiment(self, experiment_list):
            return pd.concat(experiment_list, axis=1)
    
    def filter(
        self,
        experiments: list[Experiment] = None,
        name: str | list[str] = None,
        cycle: int | list[int] = None,
        object_type: type | str | list[type | str] = None,
        inclusive:bool = True
    ) -> list[Experiment]:
        """
        General filter method to select experiments matching all given criteria.

        Args:
            name: single name or list of substrings to match in file_path
            cycle: int or list of ints
            object_type: class, class name, or list of either

        Returns:
            List of Experiment objects matching all filters.
        """
        if experiments == None:
            experiments = self.list_of_experiments

        if cycle is not None:
            try:
                cycle = int(cycle)
            except TypeError:
                return

        def name_matches(exp):
            if name is None:
                return True
            if isinstance(name, str):
                return name in exp.file_path
            return any(n in exp.file_path for n in name)

        def cycle_matches(exp):
            if cycle is None:
                return True
            if isinstance(cycle, int):
                return getattr(exp, "cycle", None) == cycle
            return getattr(exp, "cycle", None) in cycle

        def type_matches(exp):
            if object_type is None:
                return True
            types = object_type if isinstance(object_type, list) else [object_type]
            for t in types:
                if isinstance(t, str) and t.lower() in type(exp).__name__.lower():
                    return True
                if isinstance(t, type) and isinstance(exp, t):
                    return True
            return False

        if inclusive:
            #AND LOGIC
            self.filtered = [exp for exp in experiments if name_matches(exp) and cycle_matches(exp) and type_matches(exp)]
        else:
            #OR LOGIC - ONLY APPLY FILTERS THAT WERE ACTUALLY GIVEN
            active_filters = []
            if name is not None:
                #THIS IS REALLY COOL, YOU APPEND THE FUNCTIONS THAT YOU WANT TO PERFORM! CAN BE USED FOR WORKFLOWS PERHAPS?
                active_filters.append(name_matches)
            if cycle is not None:
                active_filters.append(cycle_matches)
            if object_type is not None:
                active_filters.append(type_matches)

            if active_filters:
                self.filtered = [exp for exp in experiments if any(f(exp) for f in active_filters)] #THE LAST LOGIC APPLIES THE FUNCTIONS ON THE exp AND CHECKS IF ANY ARE TRUE
        return self.filtered

    
    def filter_by_id(self, id: int|list[int]) -> list[Experiment] | Experiment: 
        
        if not isinstance(id, list):
            id = [id]
            
        id = [int(id) for id in id]
        tmp = []

        for experiment in self.list_of_experiments:
            if experiment.id in id:
                tmp.append(experiment)

        if len(tmp) == 1:
            return tmp[0]

        return tmp
        
        #ADD A MESSAGE
        print('No experiment found by given ids')

    def list_items(self, experiment_collectible = None):
        """Function to print all experiments in the form of a table 
        from a collectible of experiments
        - `experiment_collectible: list or dict of Experiment objects
        """

        x = []
        head = ['id', 'file name', 'tag', 'object type', 'No of Curves']
        tmp_tag = None
        for d in experiment_collectible:
            if d.tag != tmp_tag:
                x.append([d.id, d.file_path, d.tag, type(d).__name__])
                tmp_tag = d.tag
                if hasattr(d, 'data_list'):
                    x[-1].append(len(d.data_list))

            else:
                x.append([d.id, d.file_path])
            

        print(tabulate(x, headers=head))
        
    
    def print_chronology(self, option = 'tag'):
        '''Function that lists the experiments in chronological order'''
    
        def count_cycle(self, file_path:str):
            """Helper function for for print_chronology.
            Returns the cycle based on file_path
            
            - `file_path`: filepath of an experiment object
            """

            matches = re.findall(r'_(#\d+)', file_path)
            matches = [int(m.strip('#')) for m in matches]
            return matches if matches else [0]


        experiment_list = self.filtered
        counter = 0
        if option == 'files':

            flattened_experiment_list = experiment_list
            flattened_experiment_list.sort(key=lambda x: x.date_time)

            for experiment in flattened_experiment_list:
                cycles = count_cycle(experiment.file_path)

                if cycles[0] > counter:
                    counter = cycles [0]
                    print(messages.manager_messages['chronology'][0].format(cycle_number = counter))


                if len(cycles) > 1 and cycles[1] == 1:
                    experiment_name = type(experiment).__name__ 
                    print(messages.manager_messages['chronology'][1].format(experiment_name = experiment_name))

                print(experiment.file_path)
        else:
  
            first_experiment_list = experiment_list
            first_experiment_list.sort(key=lambda x: x.date_time)
            total_duration = first_experiment_list[-1].date_time - first_experiment_list[0].date_time

            for experiment in first_experiment_list:
                print(f'{experiment.tag}')
            print(messages.manager_messages['chronology'][2].format(total_duration = total_duration))


    def batch_process_selected_experiments(
        self,
        experiment_collectible=None,
        save_name=None,
        group_by=("tag", "cycle"),  # list or tuple of attributes
        **kwargs
    ):

        if experiment_collectible is None:
            experiment_collectible = self.filtered

        # Ensure group_by is always a tuple/list
        if isinstance(group_by, str):
            group_by = (group_by,)

        grouped_data = defaultdict(list)

        print(experiment_collectible)
        print(type(experiment_collectible))
        # Group experiments by multiple keys
        for experiment in experiment_collectible:
            key_parts = []
            for attr in group_by:
                value = getattr(experiment, attr, "NA")
                key_parts.append(str(value))
            key = tuple(key_parts)

            if not getattr(experiment, 'processed_data'):
                experiment.load_data()
                processed = experiment.process_data()
            else:
                processed = getattr(experiment, 'processed_data')

            #make multiindexed dataframe
            processed = experiment.make_multiindex(experiment.processed_data)
            grouped_data[key].append(processed)

        if save_name is None:
            save_name = input("Name of data to save: ")

        with pd.ExcelWriter(f"{save_name}.xlsx", engine="openpyxl", mode='w') as writer:
            for key_tuple, experiment_group in grouped_data.items():
                combined_df = pd.concat(experiment_group, axis=1)

                # Join tuple into safe sheet name
                sheet_name = "_".join(key_tuple)[:31]  # Excel limit
                combined_df.to_excel(writer, sheet_name=sheet_name)

        print(f"Data saved to {save_name}.xlsx")
        return experiment_collectible
    
    def set_experiments(self, data):
        """
        Setter function to set list_of_experiments, most likely from experiment_loader class
        
        Args:
            self (ExperimentManager)
            data (list)"""
        self.list_of_experiments = data

    def append_experiments(self, data):
        self.list_of_experiments += data
        

    def get_experiments(self, type_of_experiments = 'all'):
        
        match type_of_experiments:

            case 'all':
                return self.list_of_experiments
            case 'filtered':
                return self.filtered
            case 'processed':
                return self.processed_data
            

    def get_unique_experiments(self):
        #MY FIRST USE OF A SET. THE NEAT THING ABOUT THIS COLLECTION IS THE FACT THAT IT DOESNT STORE DUPLICATES!
        return list({obj.__class__.__name__ for obj in self.list_of_experiments})
        #return list({type(obj) for obj in self.list_of_experiments})
