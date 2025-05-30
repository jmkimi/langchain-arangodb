from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from libs.arangodb.langchain_arangodb.graphs.graph import ArangoGraph  # 경로는 실제 위치에 맞게 수정

class ArangoGraphRetriever(BaseRetriever):
    def __init__(self, graph: ArangoGraph, collection: str = "my_collection"):
        super().__init__()  # 오타 수정
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
            Document(page_content=doc.get("content", ""), metadata={"_key": doc.get("_key")})
            for doc in result
        ]
