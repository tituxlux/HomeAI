'''
FilConverter of ODS files
@Author: Thierry Coutelier <Thierry@Coutelier.net>  20250927
'''

import pandas as pd
from Record import Record
from FileConverter import FileConverter
from typing import Iterator

class FileConverterODS(FileConverter):
    def __init__(self, file_path: str):
        self.file_path = file_path

    def get_records(self) -> Iterator[Record]:
        xls = pd.ExcelFile(self.file_path, engine="odf")
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name, engine="odf")
            for _, row in df.iterrows():
                yield Record(
                    file_path=self.file_path,
                    sheet_name=sheet_name,
                    row=row.to_dict(),
                    headers=df.columns.tolist()
                )

