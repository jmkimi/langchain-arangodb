from abc import ABCMeta
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from langchain_core.runnables import RunnableConfig
from typing import Optional, Any
from langchain_arangodb.graphs.graph import ArangoGraph

class ArangoGraphRetriever(BaseRetriever, metaclass=ABCMeta):
    def __init__(self, graph: ArangoGraph, collection: str = "my_collection"):
        super().__init__()
        self.graph = graph
        self.collection = collection

    def invoke(
            self,
            input: str,
            config: Optional[RunnableConfig] = None,
            **kwargs: Any
    ) -> list[Document]:
        aql = f"""
        FOR doc IN {self.collection}
            FILTER CONTAINS(doc.content, @query)
            RETURN doc
        """
        result = self.graph.run_aql(aql, {"query": input})
        return [
            Document(page_content=doc.get("content", ""), metadata={"_key": doc.get("_key")})
            for doc in result
        ]
