from experiments import *
import tabulate
import re
from typing import Literal
from copy import deepcopy
from experiments.sample import Sample

class ExperimentManager():
    def __init__(self, initial_experiments: dict = None):
            self.samples: dict[str, Sample] = {}
            self.dict_of_experiments: dict[int, Experiment] = {}
            
            if initial_experiments:
                for exp in initial_experiments.values():
                    # Tutaj decydujesz o domyślnym grupowaniu
                    # Na start najlepiej użyć folderu jako nazwy próbki
                    self.add_experiment(exp, sample_name=exp.folder)

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
            experiments = self.dict_of_experiments.values()

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

    def filter_samples(self,
        name: str | list[str] = None,
        cycle: int | list[int] = None,
        object_type: type | str | list[type | str] = None,
        inclusive:bool = True 
        ):
        """
        Function to filter the sample objects based on the filtering criterion from filter function.

        Args:
            name: single name or list of substrings to match in file_path
            cycle: int or list of ints
            object_type: class, class name, or list of either

        Returns:
            sample_dict (dict): Dict of Sample:Experiment objects matching all filters.
        """
        
        sample_dict = {}
        for sample in self.samples.values():
            filtered = self.filter(sample.experiments, name, cycle, object_type, inclusive)
            if filtered:
                sample_dict[sample] = filtered
        
        return sample_dict
    
    def construct_tree(self, experiments: list[Experiment]) -> dict[Sample, list[Experiment]]:
        """
        Construct a tree of experiments based on a flat list of experiments.
        
        It is a less nested dictionary. To get a dictionary with cycle numbers, see
        coonstruct_tree_with_cycles function.
        
        Args:
            experiments (list[Experiment]): Flat list of experiments to construct the tree from.
            
        Returns:
            final_dict (dict[Sample, list[Experiment]]): Generated dictionary.
            """
        
        from collections import defaultdict

        # Defining the defaultdict
        tree = defaultdict(list)
        
        # looping through the experiments
        for experiment in experiments:

            #can also call the ExperimentManager.find_sample function
            sample_name = experiment.folder
            sample_obj = self.samples.get(sample_name)

            if sample_obj:
                tree[sample_obj].append(experiment)
        
        final_dict = dict(tree)
        return final_dict
    
    def construct_tree_with_cycles(self, experiments: list[Experiment]) -> dict[Sample, dict[int, list[Experiment]]]:
        """
        Build a nested dicionary of hierarchy Sample:Cycle:Experiments based on flat list of experiments.
        
        First level is based on the sample name, second - the cycle (int) and third: list of experiments.

        Args:
            experiments (list[Experiment]): Flat list of experiments to build the dict from.

        Returns:
            final_dict (dict[dict[list[Experiment]]]): Created nested dictionary.
        """
        from collections import defaultdict

        # Drzewo zagnieżdżone: domyślną wartością dla nowej próbki 
        # jest kolejny słownik, którego domyślną wartością jest lista
        tree = defaultdict(lambda: defaultdict(list))
        
        for experiment in experiments:

            # could also do self.manager.find_sample(experiment)
            sample_name = experiment.folder
            sample_obj = self.samples.get(sample_name)
            
            if sample_obj:
                # Wyciągamy numer cyklu (bezpiecznie, z domyślną wartością 1)
                cycle_num = getattr(experiment, 'cycle', 1)
                
                # Dodajemy eksperyment do odpowiedniego cyklu w odpowiedniej próbce
                tree[sample_obj][cycle_num].append(experiment)
        
        # this is a neat dictionary oneliner
        final_dict = {sample: dict(cycles) for sample, cycles in tree.items()}
        
        return final_dict
    
    def find_sample(self, experiment:Experiment) -> Sample | None:
        """
        A function that takes an experiment and returns its corresponding Sample object.
        
        Args:
            experiment (Experiment): Child Experiment object.
            
        Returns:
            sample_obj (Sample): Parent Sample object.
        """

        for sample_obj in self.samples.values():
            print(sample_obj)
            if experiment in sample_obj:
                return sample_obj
            else:
                continue
        return None


 
    def filter_by_id(self, id: int|list[int]) -> list[Experiment]:
        """
        Filter experiments by ther identification number (id).

        Args:
            id (int | list[int]): Test ID or list of IDs to filter by.

        Returns:
            filtered_list (list[Expeirment]): List of filtered Experiments.
        """ 
        
        if not isinstance(id, list):
            id = [id]
            
        id = [int(id) for id in id]
        filtered_list = []

        for experiment in self.dict_of_experiments:
            if experiment.id in id:
                filtered_list.append(experiment)

        return filtered_list
        

    def add_experiment(self, experiment: Experiment, sample_name: str) -> Sample:
        """
        Function that takes an Experiment object and sample_name and:
        1) creates a sample if no Sample with sample_name exist
        2) adds the experiment to the Sample

        Args:
            experiment (Experiment): Object to add.
            sample_name (str): Name of the sample.
        
        Returns:
            Sample: Sample to which experiment was added
        """

        if sample_name not in self.samples:
            self.samples[sample_name] = Sample(sample_name)
        
        self.samples[sample_name].add_experiment(experiment)
        self.dict_of_experiments[experiment.id] = experiment
        return self.samples[sample_name]
    
    def update_dict(self, data):
        """
        Setter function to set dict_of_experiments, most likely from experiment_loader class
        
        Args:
            self (ExperimentManager)
            data (list)"""
        self.dict_of_experiments.clear()
        self.dict_of_experiments.update(data)
        return self.dict_of_experiments
    
    def update_experiment(self, experiment: Experiment):
        self.dict_of_experiments[experiment.id] = experiment

    def get(self, exp_id: int | str | list[int]) -> Experiment | None | list[Experiment]:
        
        if isinstance(exp_id, (str, int)):
            try:
                exp_id = int(exp_id)
            except:
                print('Error')
            return self.dict_of_experiments[exp_id]
        
        elif isinstance(exp_id, list):
            return [self.dict_of_experiments[id] for id in exp_id]
        
    def get_all(self) -> list[Experiment] | None:
        return self.dict_of_experiments.values()
    
    def get_unique_experiments(self):
        #MY FIRST USE OF A SET. THE NEAT THING ABOUT THIS COLLECTION IS THE FACT THAT IT DOESNT STORE DUPLICATES!
        return list({obj.__class__.__name__ for obj in self.dict_of_experiments.values()})
        #return list({type(obj) for obj in self.dict_of_experiments})

    def get_experiments_by_path(self, path):
        return [exp.id for exp in self.dict_of_experiments.values() if exp.folder == path]
    
    def delete_experiment_by_id(self, key_id):
        try:
            id = int(key_id)
        except:
            return
        
        self.dict_of_experiments.pop(id, None)
        print(len(self.dict_of_experiments))

    def delete_experiment(self, exp_to_del):
        for id, exp in self.dict_of_experiments.items():
            if exp == exp_to_del:
                self.dict_of_experiments.pop(id)


    def delete_by_path(self, path):
        ids_of_experiments = self.get_experiments_by_path(path)
        for id in ids_of_experiments:
            self.delete_experiment_by_id(id)
    
    def delete_sample(self, sample:Sample):
        for exp in sample:
            self.delete_experiment_by_id(exp.id)
        self.samples.pop(sample.sample_path)

    
    def copy_experiment(self, exp_to_copy, new_id, sample_name = None):
        
        returnSample = True
        exp_copy = deepcopy(exp_to_copy)
        setattr(exp_copy, 'id', new_id)
        if sample_name is None:
            returnSample = False
            sample_name = exp_copy.folder
        sample = self.add_experiment(exp_copy, sample_name)

        if returnSample is True:
            return sample, exp_copy
        else:
            return exp_copy

    def combine_experiment(self, experiment_list):
            return pd.concat(experiment_list, axis=1)
    
    def change_class(self, experiment:Experiment, new_class:Experiment):
        try:
            new_exp = new_class(experiment.file_path,
                                experiment.date_time,
                                experiment.id,
                                'test',
                                experiment.cycle
            )
        except:
            print("Can't do")

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

            if not hasattr(experiment, 'processed_data'):
                experiment.load_all()
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

    def are_processed(self, experiments: list[Experiment]):
        """
        Quickly check if the specified experiments were processed.
        
        Args:
            experiments (list[Experiment]): Experiment list to check.
            
        Returns:
            None
        """
        for experiment in experiments:
            if not experiment.isProcessed:
                experiment.process_data()
