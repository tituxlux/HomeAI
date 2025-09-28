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
        for file_path in self.root_dir.rglob("*"):
            if file_path.suffix == ".ods":
                yield FileConverterODS(str(file_path))
            elif file_path.suffix == ".csv":
                yield FileConverterCSV(str(file_path))

