import pathlib
import tomllib
import toml  # Required to save configurations
from tabulate import tabulate

class ConfigManager():
    def __init__(self, config_file = "config.toml"):
        self.config_path = pathlib.Path(__file__).parent / config_file
        self.config = self.load_config()
        self.current_profile = None

    def load_config(self):
        """Load the configuration file"""
        with self.config_path.open(mode='rb') as fp:
            return tomllib.load(fp)
    
    def get(self, section, key, default = None):
        """Get a specific setting with an optional default value"""
        return self.config.get(section, {}).get(key, default)
    
    def set(self, section, key, value):
        """Modify a setting"""
        if section in self.config:
            self.config[section][key] = value
        else:
            self.config[section] = {key: value}

    def save_config(self):
        """Save the modified settings"""
        with self.config_path.open(mode = 'w', encoding = 'utf-8') as fp:
            toml.dump(self.config, fp)

    def list_profiles(self):
        
        profile_list = self.config['user_profiles']
        for name, parameters in profile_list.items():
            print('Profile: ', name)
            for parameter, value in parameters.items():
                to_print = f'{parameter} ({value.__class__.__name__}): {value}'
                
                if value == self.config['default_settings'][parameter]:
                    to_print = to_print + ' (default)'
                print(to_print)

    def list_settings(self, profile = None, **kwargs):

        if profile == None:
            result = ask_yes_no('No profile selected. Select profile? [y/n]')
            if result:
                self.choose_profile()
            else:
                return

        list_of_settings = list(self.config['user_profiles'][profile].keys())

        for number, x in enumerate(self.config['user_profiles'][profile].keys(), start = 1):
            print(f'{number}. {x}')

        inpt = int(input('Choose option')) - 1
        x = list_of_settings[inpt]
        print(x)



    def choose_profile(self):

        if self.current_profile != None:
            print(f'Current profile: {self.current_profile}')
            answer = input('Continue? [y/n]: ')
            if answer == 'y':
                pass
            else:
                return
            
        for i, profile in enumerate(self.config['user_profiles']):
                print(f'{i}. {profile}') 
                selected_profile = input('Select a profile by providing an index or name: ')
        try:
            self.config['user_profiles'][selected_profile]
        except:
            print(f'No profile with name {selected_profile}')
            self.choose_profile()

        print(f'Selected profile "{selected_profile}"')
        self.current_profile = selected_profile
            
    
def main():
    tmp = ConfigManager()
    while True:
        print(f'Current profile:',tmp.current_profile)
        answer = input(('''
              1. Load config
              2. Choose profile
              3. Settings\n'''))
        match answer:

            case "1":
                tmp.load_config()
            case "2":
                tmp.choose_profile()
            case "3":
                tmp.list_settings(profile = tmp.current_profile)

def ask_yes_no(string):
    tmp = input(string)
    if tmp in any(['yes', 'y', 'YES', 'Y']):
        return True
    elif tmp in any(['no', 'n', 'N', 'NO']):
        return False
    else:
        print(f'No option {tmp}')
        ask_yes_no(string)

main()
