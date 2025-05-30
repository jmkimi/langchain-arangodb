from unittest.mock import MagicMock
import pytest
from langchain_core.documents import Document
from langchain_arangodb.retriever.retriever import ArangoGraphRetriever

@pytest.fixture
def mock_retriever():
    mock_graph = MagicMock()
    mock_graph.run_aql.return_value = [
        {"_key": "doc1", "content": "이 문서는 인공지능에 관한 설명입니다."}
    ]
    return ArangoGraphRetriever(graph=mock_graph, collection="actor")

def test_mocked_retrieval(mock_retriever):
    results = mock_retriever.invoke("인공지능")

    assert isinstance(results, list)
    assert all(isinstance(doc, Document) for doc in results)
    assert results[0].page_content == "이 문서는 인공지능에 관한 설명입니다."