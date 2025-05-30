import numpy as np

from typing import List, Optional, Dict, Any
from hashlib import md5
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore
from langchain_core.vectorstores.utils import maximal_marginal_relevance
from langchain_arangodb.vectorstores.utils import DistanceStrategy


class ArangoVector(VectorStore):
    def __init__(
            self,
            embedding: Embeddings,
            *,
            db_url: str,
            username: str,
            password: str,
            database: str,
            collection_name: str,
            embedding_field: str = "embedding",
            text_field: str = "text",
            distance_strategy: DistanceStrategy = DistanceStrategy.COSINE,
    ):
        self.embedding = embedding
        self.db_url = db_url
        self.username = username
        self.password = password
        self.database = database
        self.collection_name = collection_name
        self.embedding_field = embedding_field
        self.text_field = text_field
        self._distance_strategy = distance_strategy

        # TODO: Initialize ArangoDB client and collection handle
        self.collection = None  # Placeholder

    @classmethod
    def from_texts(
            cls,
            texts: List[str],
            embedding: Embeddings,
            metadatas: Optional[List[dict]] = None,
            ids: Optional[List[str]] = None,
            **kwargs: Any,
    ) -> "ArangoVector":
        embeddings = embedding.embed_documents(texts)
        return cls.__from(
            texts=texts,
            embeddings=embeddings,
            embedding=embedding,
            metadatas=metadatas,
            ids=ids,
            **kwargs,
        )

    @classmethod
    def __from(
            cls,
            texts: List[str],
            embeddings: List[List[float]],
            embedding: Embeddings,
            metadatas: Optional[List[dict]] = None,
            ids: Optional[List[str]] = None,
            **kwargs: Any,
    ) -> "ArangoVector":
        if ids is None:
            ids = [md5(text.encode("utf-8")).hexdigest() for text in texts]

        if not metadatas:
            metadatas = [{} for _ in texts]

        store = cls(embedding=embedding, **kwargs)
        store.add_embeddings(texts=texts, embeddings=embeddings, metadatas=metadatas, ids=ids)
        return store

    def add_embeddings(
            self,
            texts: List[str],
            embeddings: List[List[float]],
            metadatas: Optional[List[dict]] = None,
            ids: Optional[List[str]] = None,
            **kwargs: Any,
    ) -> List[str]:
        if ids is None:
            ids = [md5(text.encode("utf-8")).hexdigest() for text in texts]

        if not metadatas:
            metadatas = [{} for _ in texts]

        documents = []
        for text, embedding, metadata, doc_id in zip(texts, embeddings, metadatas, ids):
            doc = {
                "_key": doc_id,
                self.text_field: text,
                self.embedding_field: embedding,
                **metadata,
            }
            documents.append(doc)

        # TODO: Insert documents into ArangoDB
        # Example: self.collection.import_bulk(documents)

        return ids

    def similarity_search(
            self,
            query: str,
            k: int = 4,
            filter: Optional[Dict[str, Any]] = None,
            **kwargs: Any,
    ) -> List[Document]:
        query_embedding = self.embedding.embed_query(query)
        return self.similarity_search_by_vector(
            embedding=query_embedding, k=k, filter=filter, **kwargs
        )

    def similarity_search_by_vector(
            self,
            embedding: List[float],
            k: int = 4,
            filter: Optional[Dict[str, Any]] = None,
            **kwargs: Any,
    ) -> List[Document]:
        return_embeddings = kwargs.get("return_embeddings", False)
        # TODO: Perform vector similarity search using ArangoDB's AQL or Search Views
        # This is a placeholder return with mock documents
        results = []

        # Example:
        # query = "FOR doc IN vector_collection ... SORT ... LIMIT ... RETURN doc"
        # bind_vars = {...}
        # cursor = db.aql.execute(query, bind_vars=bind_vars)
        # for record in cursor:
        #     metadata = record.copy()
        #     text = metadata.pop(self.text_field)
        #     if return_embeddings:
        #         metadata["_embedding_"] = record[self.embedding_field]
        #     results.append(Document(page_content=text, metadata=metadata))

        return results

    def max_marginal_relevance_search(
            self,
            query: str,
            k: int = 4,
            fetch_k: int = 20,
            lambda_mult: float = 0.5,
            filter: Optional[Dict[str, Any]] = None,
            **kwargs: Any,
    ) -> List[Document]:
        query_embedding = self.embedding.embed_query(query)
        initial_results = self.similarity_search_by_vector(
            embedding=query_embedding,
            k=fetch_k,
            filter=filter,
            return_embeddings=True,
            **kwargs,
        )

        embeddings = [doc.metadata.get("_embedding_") for doc in initial_results]
        selected_indices = maximal_marginal_relevance(
            np.array(query_embedding), embeddings, lambda_mult=lambda_mult, k=k
        )
        selected_docs = [initial_results[i] for i in selected_indices]

        for doc in selected_docs:
            if "_embedding_" in doc.metadata:
                del doc.metadata["_embedding_"]

        return selected_docs
