'''
Class to write Vectores to DB
@author: Thierry Coutelier <Thierry@Coutelier.net>  20250927
@description: Write chunks to a vector database using embeddings from a specified model.
@license: GPL-3.0
'''


from sentence_transformers import SentenceTransformer
import chromadb
from Chunk import Chunk

class VectorDBWriter:
    def __init__(self, db_path: str, model: str = "all-MiniLM-L6-v2"):
        self.db_path = db_path
        self.embedding_model = SentenceTransformer(model)
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection("comptes")

    def write_chunks(self, chunks: list[Chunk]):
        embeddings = self.embedding_model.encode([c.content for c in chunks])
        self.collection.add(
            embeddings=embeddings.tolist(),
            documents=[c.content for c in chunks],
            metadatas=[c.metadata for c in chunks],
            ids=[f"id_{i}" for i in range(len(chunks))]
        )

