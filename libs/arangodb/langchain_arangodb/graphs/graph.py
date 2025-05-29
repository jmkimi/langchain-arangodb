from arango import ArangoClient
from typing import Optional

class ArangoGraph:
    def __init__(
            self,
            db_name: str = "test",
            username: str = "root",
            password: Optional[str] = None,
            host: str = "http://localhost:8529"
    ):
        client = ArangoClient()
        self.db = client.db(db_name, username=username, password=password)

    def run_aql(self, query: str, bind_vars: Optional[dict] = None) -> list[dict]:
        cursor = self.db.aql.execute(query, bind_vars=bind_vars or {})
        return list(cursor)
