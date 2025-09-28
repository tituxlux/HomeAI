'''
Chunk data
@author: Thierry Coutelier <Thierry@Coutelier.net>  20250927
@description: Data class to represent a chunk of text with associated metadata.
@license: GPL-3.0

'''

from dataclasses import dataclass

@dataclass
class Chunk:
    content: str
    metadata: dict

