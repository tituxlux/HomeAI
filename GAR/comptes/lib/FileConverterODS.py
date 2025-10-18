'''
FilConverter of ODS files
@Author: Thierry Coutelier <Thierry@Coutelier.net>  20250927
'''

import pandas as pd
from Record import Record
from FileConverter import FileConverter
from typing import Iterator

class FileConverterODS(FileConverter):
    def __init__(self, file_path: str, sheet_name: str = None):
        self.file_path = file_path
        self.sheet_name = sheet_name  # If None, process all sheets
        
        
    def get_sheet_names(self) -> Iterator[str]:
        xls = pd.ExcelFile(self.file_path, engine="odf")
        for sheet in xls.sheet_names:
            yield sheet

    def get_records(self):
        """Yield Record objects for each row in the specified sheet or all sheets."""
        if self.sheet_name is None:
            for sheet in self.get_sheet_names():
                df = pd.read_excel(self.file_path, sheet_name=sheet, engine="odf")
                for _, row in df.iterrows():
                    yield Record(
                        file_path=self.file_path,
                        sheet_name=sheet,
                        row=row.to_dict(),  # Dict of column_name → value
                        headers=list(df.columns),
                    )
        else:
            df = pd.read_excel(self.file_path, sheet_name=self.sheet_name, engine="odf")
            for _, row in df.iterrows():
                yield Record(
                    file_path=self.file_path,
                    sheet_name=self.sheet_name,
                    row=row.to_dict(),  # Dict of column_name → value
                    headers=list(df.columns),
                )
