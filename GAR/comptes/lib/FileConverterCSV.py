'''
FilConverter for CSV files
@Author: Thierry Coutelier <Thierry@Coutelier.net>  20250927

'''

import pandas as pd
from Record import Record
from FileConverter import FileConverter
from typing import Iterator

class FileConverterCSV(FileConverter):
    def __init__(self, file_path: str, delimiter: str = ";", encoding: str = "utf-8"):
        self.file_path = file_path
        self.delimiter = delimiter
        self.encoding = encoding

    def get_records(self) -> Iterator[Record]:
        df = pd.read_csv(self.file_path, delimiter=self.delimiter, encoding=self.encoding)
        for _, row in df.iterrows():
            yield Record(
                file_path=self.file_path,
                sheet_name="sheet1",  # CSV has no sheets
                row=row.to_dict(),
                headers=df.columns.tolist()
            )


