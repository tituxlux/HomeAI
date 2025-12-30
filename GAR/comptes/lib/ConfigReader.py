'''
@author: Thierry Coutelier <Thierry@Coutelier.net>  20250927
@description: Configuration reader module
   Load an yml configuration file and provide access to its contents.
@license: GPL-3.0

'''

import yaml
import os
from find_file import FileFinder

class ConfigReader:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config_path = FileFinder().find_file(self.config_path)
        self.config = self._load_config()


        
    def _load_config(self) -> dict:
        with open(self.config_path, 'r') as file:
            return yaml.safe_load(file)

    def get(self, key: str, default=None):
        return self.config.get(key, default)

    def get_all(self) -> dict:
        return self.config

