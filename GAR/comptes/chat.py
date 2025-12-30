#!/usr/bin/env python3
"""
Chat interface for GAR comptes project.
Uses ChromaDB for vector search and Mistral LLM for answering questions.
"""
import logging
from pathlib import Path
from typing import Dict, Any, List
import chromadb
from chromadb.utils import embedding_functions
from llama_cpp import Llama

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComptesChat:
    def __init__(self, config_path: str = "config.yml"):
        self.config = self._load_config(config_path)
        self._configure_logging()

        # Initialize ChromaDB client
        self.chroma_client = chromadb.PersistentClient(
            path=str(Path(self.config["vector_db"]["persist_directory"]).absolute())
        )
        self.collection = self.chroma_client.get_collection(f"{self.config['project']['tenant']}_data")

        # Initialize LLM
        self.llm = Llama(
            model_path=str(Path(self.config["model"]["type"]).expanduser().absolute()),
            n_gpu_layers=self.config["model"]["n_gpu_layers"],
            n_ctx=self.config["model"]["n_ctx"],
            chat_format=self.config["model"]["chat_format"]
        )

        # Initialize embedding function
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=self.config["embedding"]["model"]
        )

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        import yaml
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _configure_logging(self):
        """Configure logging based on config."""
        log_level = self.config["logging"]["level"].upper()
        logger.setLevel(getattr(logging, log_level))

        log_file = self.config["logging"].get("log_file")
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(getattr(logging, log_level))
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(file_handler)

    def query_vector_db(self, question: str, n_results: int = 5) -> Dict:
        """Query the vector database for relevant documents."""
        return self.collection.query(
            query_texts=[question],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )

    def generate_answer(self, question: str, context: str) -> str:
        """Generate an answer using the LLM."""
        prompt = f"""[INST]
        You are a helpful financial assistant. Use the following context to answer the question.
        If you don't know the answer, say you don't know. Be concise and data-driven.

        Context:
        {context}

        Question: {question}[/INST]"""

        response = self.llm.create_chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1000
        )
        return response["choices"][0]["message"]["content"]

    def chat(self):
        """Start an interactive chat session."""
        print(f"Welcome to {self.config['project']['name']} Chat!")
        print("Type 'quit' or 'exit' to end the session.\n")

        while True:
            try:
                question = input("You: ")
                if question.lower() in ['quit', 'exit']:
                    break

                # Query vector DB
                results = self.query_vector_db(question)

                # Build context
                context = []
                for doc, meta, dist in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0]
                ):
                    context.append(
                        f"Source: {meta.get('file', 'unknown')} (Sheet: {meta.get('sheet', 'N/A')}, Distance: {dist:.3f})\n"
                        f"Content: {doc}\n"
                    )

                if not context:
                    print("Assistant: No relevant documents found in the database.")
                    continue

                context_str = "\n\n".join(context)

                # Generate answer
                answer = self.generate_answer(question, context_str)
                print(f"Assistant: {answer}\n")

            except KeyboardInterrupt:
                print("\nSession ended by user.")
                break
            except Exception as e:
                logger.error(f"Error during chat: {e}")
                print(f"Assistant: An error occurred. Please try again.")

def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description="Chat interface for GAR comptes project.")
    parser.add_argument(
        "--config",
        type=str,
        default="config.yml",
        help="Path to the configuration YAML file."
    )
    return parser.parse_args()
if __name__ == "__main__":
    args = parse_args()
    chat = ComptesChat(config_path=args.config)
    chat.chat()
