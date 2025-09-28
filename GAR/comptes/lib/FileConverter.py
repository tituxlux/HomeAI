'''
Abstract Class for converting the files
  @author: Thierry Coutelier <Thierry@Coutelier.net>  20250927
  @description: Abstract base class for file converters.
  @license: GPL-3.0

'''

from abc import ABC, abstractmethod
from typing import Iterator
from Record import Record

class FileConverter(ABC):
    @abstractmethod
    def get_records(self) -> Iterator[Record]:
        pass

