import pytest
from langchain_core.documents import Document
from langchain_arangodb.graphs.graph import ArangoGraph
from langchain_arangodb.retriever.retriever import ArangoGraphRetriever

@pytest.fixture
def retriever() -> ArangoGraphRetriever:
    graph = ArangoGraph(
        password="openSesame",  # TODO: 실제 비밀번호로 교체
        db_name="_system",
        hosts="http://localhost:8529"
    )
    return ArangoGraphRetriever(graph=graph, collection="actor")

def test_basic_retrieval(retriever):
    query = "인공지능"
    results = retriever.invoke(query)

    assert isinstance(results, list), "Result should be a list"
    assert all(isinstance(doc, Document) for doc in results), "Each result should be a Document"
    assert all(hasattr(doc, "page_content") for doc in results), "Each Document should have page_content"
