'''
LLM Analyzer to use an LLM to understand our files
@author: Thierry Coutelier <Thierry@Coutelier.net>  20250927
@description: Use an LLM (Ollama) to analyze files and suggest chunking strategies for semantic search.
@license: GPL-3.0 

'''

from Record import Record
from Chunk import Chunk
import ollama  # Assuming ollama is a library to interact with the Ollama API

class LLMAnalyzer:
    def __init__(self, model: str = "mistral:8x7b"):
        self.model = model

    def analyze_file(self, file_path: str, sample_records: list[Record]) -> dict:
        prompt = f"""
        Analyze the following file and sample records.
        File: {file_path}
        Sample records: {sample_records[:3]}
        ---
        1. Describe the purpose of this file.
        2. For each sheet/table, describe the columns and their meaning.
        3. Suggest how to chunk this data for semantic search.
        4. Note any patterns, relationships, or anomalies.
        """
        # Call Ollama API
        response = ollama.chat(model=self.model, messages=[{"role": "user", "content": prompt}])
        return {"analysis": response["message"]["content"]}

