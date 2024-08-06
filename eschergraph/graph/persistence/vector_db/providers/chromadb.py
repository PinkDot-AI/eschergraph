from eschergraph.graph.persistence.vector_db.vector_db import VectorDB
import chromadb

class ChromaDB(VectorDB):
    def __init__(self):
        self.client = chromadb.Client()

    def connect(self):
        # Code to connect to ChromaDB
        pass

    def create_collection(self, name:str) -> None:
        self.collection = self.client.create_collection(name=name)

    def input_documents(self, embeddings:list[list[float]], documents:list[str], ids:list[str], metadata:list[dict], collection_name:str):
        collection = self.client.get_collection(name = collection_name)
        collection.add(
            documents = documents,
            ids = ids,
            embeddings = embeddings,
            metadatas = metadata,
        )

    def search(self, embedding:list[float], top_n:int, metadata:dict, collection_name:str):
        collection = self.client.get_collection(name = collection_name)
        results = collection.query(
            query_embeddings = [embedding],
            n_results = top_n,
            where = metadata,
            include=["documents"]
        )

        return results
