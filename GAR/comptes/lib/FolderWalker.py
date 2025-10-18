'''
FolderWalker to recursuvely go throug all of the files recursively
and instatiate the right FileConverter
@Author: Thierry Coutelier <Thierry@Coutelier.net>  20250927
'''

from pathlib import Path
from typing import Iterator
from FileConverter import FileConverter
from FileConverterODS import FileConverterODS
from FileConverterCSV import FileConverterCSV

class FolderWalker:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)

    def walk(self) -> Iterator[FileConverter]:
        """Yield a FileConverterODS for each sheet in each ODS file."""
        for ods_file in Path(self.root_dir).glob("*.ods"):
            converter = FileConverterODS(file_path=str(ods_file))
            for sheet_name in converter.get_sheet_names():
                yield FileConverterODS(file_path=str(ods_file), sheet_name=sheet_name)
        for csv_file in Path(self.root_dir).glob("*.csv"):
            yield FileConverterCSV(file_path=str(csv_file))
        for csv_file in Path(self.root_dir).glob("*.CSV"):
            yield FileConverterCSV(file_path=str(csv_file))
        