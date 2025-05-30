from arango.client import ArangoClient
from typing import Optional, Union, Sequence


class ArangoGraph:
    def __init__(
        self,
        db_name: str = "_system",
        username: str = "root",
        password: Optional[str] = None,
        hosts: Union[str, Sequence[str]] = "http://localhost:8529"
    ):
        self.client = ArangoClient(hosts=hosts)
        self.db = self.client.db(db_name, username=username, password=password)

    def run_aql(self, query: str, bind_vars: Optional[dict] = None) -> list[dict]:
        try:
            cursor = self.db.aql.execute(query, bind_vars=bind_vars or {})
            return list(cursor)
        except Exception as e:
            raise RuntimeError(f"AQL execution failed: {e}")
