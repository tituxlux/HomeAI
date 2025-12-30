    
import os

USUAL_NAMES= [ 'config.yml', 'config.yaml' ]
USUAL_FOLDERS = [
    '.', 'GAR', 'GAR/comptes',
    'config', 'configs', 'configuration', 'configurations'
]

class FileFinder:
    def __init__(self, config_path: str = '', **kwargs):
        if 'ususal_names' in kwargs:
            self.usual_names = kwargs['ususal_names']
        else:
            self.usual_names = USUAL_NAMES
        if 'ususal_folders' in kwargs:
            self.usual_folders = kwargs['ususal_folders']
        else:
            self.usual_folders = USUAL_FOLDERS
        self.config_path = config_path
        if 'max_up' in kwargs:
            self.max_up = kwargs['max_up']
        else:
            self.max_up = 3

    def find_file(self, config_path: str = '') -> str:
        ''' Find a configuration file by searching usual folders and names.
        
        :param config_path: Initial configuration file path if not set try USUAL_FOLDERS and USUAL_NAMES
        :type config_path: str
        :return: Path to the found configuration file
        :rtype: str
        :raises FileNotFoundError: If the configuration file is not found
        ''' 
        if config_path and os.path.exists(config_path):
            return config_path
        if self.config_path and os.path.exists(self.config_path):
            return self.config_path
        depth = self.max_up
        up_path = '.'
        while depth > 0:
            depth -= 1            
            for folder in self.usual_folders:
                possible_path = os.path.join(up_path, folder, config_path)
                if os.path.exists(possible_path):
                    return possible_path

                for name in self.usual_names:
                    possible_path = os.path.join(up_path, folder, name)
                    if os.path.exists(possible_path):
                        return possible_path
            up_path = os.path.join(up_path, '..')
        raise FileNotFoundError(f"Configuration file '{config_path}' not found.")