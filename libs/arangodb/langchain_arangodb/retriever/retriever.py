from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from langchain_arangodb.graphs.graph import ArangoGraph

class ArangoGraphRetriever(BaseRetriever):
    def __init__(self, graph: ArangoGraph, collection: str = "my_collection"):
        self.graph = graph
        self.collection = collection

    def get_relevant_documents(self, query: str) -> list[Document]:
        aql = f"""
        FOR doc IN {self.collection}
            FILTER CONTAINS(doc.content, @query)
            RETURN doc
        """
        result = self.graph.run_aql(aql, {"query": query})
        return [
            Document(page_content=doc["content"], metadata={"_key": doc["_key"]})
            for doc in result
        ]
