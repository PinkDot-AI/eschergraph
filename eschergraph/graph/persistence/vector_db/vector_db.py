from abc import ABC, abstractmethod

class VectorDB(ABC):
    @abstractmethod
    def connect(self) -> None:
        pass
    
    @abstractmethod
    def create_collection(self, name:str):
        """
        Crete a collection with a given name

        Parameters:
        name (str) name for the collection
        """
        pass

    @abstractmethod
    def input_documents(self, 
                        embeddings: list[list[float]], 
                        documents: list[str], 
                        ids: list[int], 
                        metadata: list[dict[str, any]], 
                        collection_name:str) -> None:
        """
        Store documents with their embeddings, ids, and metadata.

        Parameters:
        embedding (List[List[float]]): List of embeddings for the documents.
        document (List[str]): List of document texts.
        ids (List[int]): List of document IDs.
        metadata (List[Dict[str, Any]]): List of metadata dictionaries.
        """
        pass

    @abstractmethod
    def search(self, embedding: list[list[float]], top_n: int, metadata: dict[str, any], collection_name:str) -> list[dict[str, any]] :
        """
        Search for the top_n documents that are most similar to the given embedding.

        Parameters:
        embedding (List[float]): Embedding of the query document.
        top_n (int): Number of top documents to retrieve.
        metadata (Dict[str, Any]): Metadata to filter the search results.

        Returns:
        List[Dict[str, Any]]: List of documents that match the query.
        """
        pass
