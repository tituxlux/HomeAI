'''
Representation of One record giving access to the data in a structured way
@author: Thierry Coutelier <Thierry@Coutelier.net>  20250927
@description: Data class to represent a record from a file, including its path, sheet name, row data, and headers.
@license: GPL-3.0

'''

from dataclasses import dataclass
from typing import Dict, Any, List
@dataclass
class Record:
    """Represents a single record (row) from a spreadsheet or CSV."""
    file_path: str      # Path to the source file
    sheet_name: str     # Name of the sheet (or empty for CSV)
    row: Dict[str, Any] # Row data as {column_name: value}
    headers: List[str]  # List of column headers (for context)