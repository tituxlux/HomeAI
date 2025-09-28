'''
Representation of One record giving access to the data in a structured way
@author: Thierry Coutelier <Thierry@Coutelier.net>  20250927
@description: Data class to represent a record from a file, including its path, sheet name, row data, and headers.
@license: GPL-3.0

'''

from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class Record:
    file_path: str
    sheet_name: str
    row: Dict[str, Any]
    headers: list


