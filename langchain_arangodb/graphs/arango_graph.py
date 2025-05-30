from hashlib import md5
from typing import Any, Dict, List, Optional

from langchain_arangodb.graphs.graph_store import GraphStore
from langchain_arangodb.graphs.graph_document import GraphDocument
from arango.client import ArangoClient
from arango.database import StandardDatabase


class ArangoGraph(GraphStore):
    def __init__(
        self,
        hosts: str = "http://localhost:8529",
        username: str = "root",
        password: Optional[str] = None,
        db_name: str = "_system",
        enhanced_schema: bool = False,
    ) -> None:
        self.client = ArangoClient(hosts=hosts)
        self.db: StandardDatabase = self.client.db(db_name, username=username, password=password)
        self.schema = ""
        self.structured_schema: Dict[str, Any] = {}
        self._enhanced_schema = enhanced_schema

    def query(self, aql: str, bind_vars: dict = {}) -> List[Dict[str, Any]]:
        cursor = self.db.aql.execute(aql, bind_vars=bind_vars)
        return list(cursor)

    @property
    def get_schema(self) -> str:
        return self.schema

    @property
    def get_structured_schema(self) -> Dict[str, Any]:
        return self.structured_schema

    def refresh_schema(self) -> None:
        # Placeholder: should be implemented with custom AQL to introspect collections and fields
        self.schema = "(Schema inspection not implemented for ArangoDB)"
        self.structured_schema = {}

    def add_graph_documents(
        self,
        graph_documents: List[GraphDocument],
        include_source: bool = False,
        baseEntityLabel: bool = False,
    ) -> None:
        for document in graph_documents:
            for node in document.nodes:
                doc = node.properties.copy()
                doc["_key"] = node.id
                doc["_type"] = node.type
                self.db.collection(node.type).insert(doc, overwrite=True)

            for rel in document.relationships:
                edge_collection = rel.type.replace(" ", "_").lower()
                edge = rel.properties.copy()
                edge["_from"] = f"{rel.source.type}/{rel.source.id}"
                edge["_to"] = f"{rel.target.type}/{rel.target.id}"
                self.db.collection(edge_collection).insert(edge, overwrite=True)

            if include_source and document.source:
                if not document.source.metadata.get("id"):
                    document.source.metadata["id"] = md5(document.source.page_content.encode("utf-8")).hexdigest()
                doc = {
                    "_key": document.source.metadata["id"],
                    "text": document.source.page_content,
                    **document.source.metadata,
                }
                self.db.collection("Document").insert(doc, overwrite=True)

    def close(self) -> None:
        # Nothing to close for arango-python driver
        pass

    def __enter__(self) -> "ArangoGraph":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def __del__(self) -> None:
        self.close()
