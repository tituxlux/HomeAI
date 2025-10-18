'''
LLM Analyzer to use an LLM to understand our files
@author: Thierry Coutelier <Thierry@Coutelier.net>  20250927
@description: Use an LLM (Ollama) to analyze files and suggest chunking strategies for semantic search.
@license: GPL-3.0 

'''

from Record import Record
from llama_cpp import Llama
from typing import List, Dict, Any
import logging
from os import path
from pathlib import Path
logger = logging.getLogger(__name__)


class LLMAnalyzer:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        try:
            
            self.llm = Llama(
                model_path=str(Path(self.config["model"]["type"]).expanduser()),
                n_gpu_layers=self.config["model"].get("n_gpu_layers", 32),
                n_ctx=self.config["model"].get("n_ctx", 4096),
                chat_format=self.config["model"].get("chat_format", "mistral-instruct"),
            )
            logger.info("LLM loaded with GPU acceleration")
        except Exception as e:
            logger.error(f"Failed to load LLM: {e}")
            raise

    def analyze_file(self, file_path: str, records: List[Record]) -> str:
        """Analyze file content using LLM."""
        try:
            context = "\n".join(f"Row {i}: {record.row}"  for i, record in enumerate(records, 1) )
            prompt = f"""[INST]
            Analyze the following financial data from {file_path}:
            {context}
            Provide a concise summary and highlight anomalies.[/INST]"""
            response = self.llm.create_chat_completion(
                messages=[{"role": "user", "content": prompt}]
            )
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return "Analysis failed"
