'''
Ingest folders
@Author: Thierry Coutelier <Thierry@Coutelier.net>  20250927
@License: GPL-3.0
@Description: Ingest files from a folder, analyze them with LLM, and store results in a vector database.
@Requires: ConfigReader, FolderWalker, LLMAnalyzer, VectorDBWriter
@Requires: Some LLM model accessible via Ollama or SentenceTransformers

'''
import logging
# Instantiate a logger
logger = logging.getLogger(__name__)

# Set the library path for our own classes
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))
from ConfigReader import ConfigReader
from FolderWalker import FolderWalker
from LLMAnalyzer import LLMAnalyzer
from VectorDBWriter import VectorDBWriter
from Chunk import Chunk
from Record import Record

def ingest_folder(root_dir: str, db_path: str):
    walker = FolderWalker(root_dir)
    analyzer = LLMAnalyzer()
    writer = VectorDBWriter(db_path)

    for converter in walker.walk():
        records = list(converter.get_records())
        analysis = analyzer.analyze_file(converter.file_path, records)

        # Create chunks based on LLM analysis
        chunks = []
        for record in records:
            chunk = Chunk(
                content=f"{record.file_path} | {record.sheet_name} | {record.row}",
                metadata={
                    "file": record.file_path,
                    "sheet": record.sheet_name,
                    "analysis": analysis
                }
            )
            chunks.append(chunk)

        writer.write_chunks(chunks)

def load_config(config_path: str) -> dict:    
    config_reader = ConfigReader(config_path)
    return config_reader.get_all()

def configure_logging(logger, config: dict):

    level = config.get("logging.level", "INFO").upper()
    if level == "DEBUG":
        logger.setLevel(logging.DEBUG)
    elif level == "WARNING":
        logger.setLevel(logging.WARNING)
    elif level == "ERROR":
        logger.setLevel(logging.ERROR)
    else:
        logger.setLevel(logging.INFO)
    logging.basicConfig(level=level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # We have logging: log_file: XXX  log to file if needed
    log_file = config.get("logging.log_file", None)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    logging.getLogger("chromadb").setLevel(level)
    logging.getLogger("ollama").setLevel(level)
    logging.getLogger("sentence_transformers").setLevel(level)

if __name__ == "__main__":
    # Load configuration
    config = load_config("GAR/comptes/config.yml")
    configure_logging(logger, config)
    root_dir = config.get("root_dir", "./data")
    db_path = config.get("db_path", "./vector_db")
    logger.debug(f"Configuration loaded: root_dir={root_dir}, db_path={db_path}")
    ingest_folder(root_dir, db_path)
