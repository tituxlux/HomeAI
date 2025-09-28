'''
Ingest folders with llama.cpp GPU support
@Author: Thierry Coutelier <Thierry@Coutelier.net>  20250928
@License: GPL-3.0
'''
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Set library path
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))

# Load environment (Intel oneAPI)
os.environ["ZES_ENABLE_SYSMAN"] = "1"  # Silence SYCL warnings
source_oneapi = "/opt/intel/oneapi/setvars.sh"
if os.path.exists(source_oneapi):
    os.system(f"source {source_oneapi} >/dev/null 2>&1")

# Initialize logger
logger = logging.getLogger(__name__)

# Import custom classes
from ConfigReader import ConfigReader
from FolderWalker import FolderWalker
from VectorDBWriter import VectorDBWriter
from Chunk import Chunk
from Record import Record

#

def ingest_folder(root_dir: str, db_path: str, config: Dict[str, Any]):
    walker = FolderWalker(root_dir)
    analyzer = LLMAnalyzer(config)
    writer = VectorDBWriter(db_path)

    for converter in walker.walk():
        records = list(converter.get_records())
        analysis = analyzer.analyze_file(converter.file_path, records)

        # Create chunks
        chunks = [
            Chunk(
                content=f"{record.file_path} | {record.sheet_name} | {record.row}",
                metadata={
                    "file": record.file_path,
                    "sheet": record.sheet_name,
                    "analysis": analysis,
                    "model": config["embedding"]["model"],
                }
            )
            for record in records
        ]
        writer.write_chunks(chunks)
        logger.debug(f"Processed {len(chunks)} chunks from {converter.file_path}")

def load_config(config_path: str) -> Dict[str, Any]:
    config_reader = ConfigReader(config_path)
    config = config_reader.get_all()
    # Fix path for model
    if config["model"]["type"].startswith("models/"):
        config["model"]["type"] = str(Path.home() / "src" / config["model"]["type"])
    return config

def configure_logging(config: Dict[str, Any]):
    level = config.get("logging", {}).get("level", "INFO").upper()
    numeric_level = getattr(logging, level, logging.INFO)

    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )

    # File logging
    log_file = config.get("logging", {}).get("log_file")
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(file_handler)

    # Silence noisy libraries
    for lib in ["chromadb", "sentence_transformers", "llama_cpp"]:
        logging.getLogger(lib).setLevel(logging.WARNING)

if __name__ == "__main__":
    # Load config
    config = load_config("GAR/comptes/config.yml")
    configure_logging(config)

    # Validate paths
    root_dir = config.get("data_sources", [{}])[0].get("path", "./data")
    db_path = config.get("vector_db", {}).get("persist_directory", "./data/vector_db")
    os.makedirs(db_path, exist_ok=True)

    logger.info(f"Starting ingestion: {root_dir} -> {db_path}")
    logger.debug(f"Config: {config}")

    ingest_folder(root_dir, db_path, config)
    logger.info("Ingestion complete")
