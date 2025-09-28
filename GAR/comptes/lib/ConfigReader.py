'''
@author: Thierry Coutelier <Thierry@Coutelier.net>  20250927
@description: Configuration reader module
   Load an yml configuration file and provide access to its contents.
@license: GPL-3.0

'''

import yaml
import os

class ConfigReader:
    def __init__(self, config_path: str):
        self.config_path = config_path
        # Guess path if needed
        if self.config_path == "config.yml":
            import os
            self.config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config.yml')
        self.config = self._load_config()


    def _guess_config_path(self) -> str:
        while not os.path.exists(self.config_path):
            parent = os.path.dirname(os.path.dirname(self.config_path))
            if parent == self.config_path:  # Reached root directory
                raise FileNotFoundError(f"Configuration file '{self.config_path}' not found.")
            self.config_path = os.path.join(parent, 'config.yml')
        return self.config_path
    
    def _load_config(self) -> dict:
        with open(self.config_path, 'r') as file:
            return yaml.safe_load(file)

    def get(self, key: str, default=None):
        return self.config.get(key, default)

    def get_all(self) -> dict:
        return self.config

