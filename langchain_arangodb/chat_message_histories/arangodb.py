from typing import List, Optional, Union
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, messages_from_dict
from langchain_arangodb.graphs.graph import ArangoGraph


class ArangoChatMessageHistory(BaseChatMessageHistory):
    """Chat message history stored in an ArangoDB collection."""

    def __init__(
            self,
            session_id: Union[str, int],
            *,
            graph: Optional[ArangoGraph] = None,
            collection: str = "chat_history",
            password: Optional[str] = None,
            db_name: str = "_system",
            username: str = "root",
            hosts: Union[str, List[str]] = "http://localhost:8529",
            window: int = 3,
    ):
        if not session_id:
            raise ValueError("session_id must be provided")

        self._session_id = str(session_id)
        self._collection = collection
        self._window = window

        if graph:
            self._graph = graph
        else:
            self._graph = ArangoGraph(
                db_name=db_name,
                username=username,
                password=password,
                hosts=hosts,
            )

        # Ensure collection exists (optional: add init script if needed)
        if not self._graph.db.has_collection(self._collection):
            self._graph.db.create_collection(self._collection)

    @property
    def messages(self) -> List[BaseMessage]:
        query = f"""
        FOR doc IN {self._collection}
            FILTER doc.session_id == @session_id
            SORT doc.timestamp ASC
            LIMIT @limit
            RETURN {{ type: doc.role, data: doc.content }}
        """
        results = self._graph.run_aql(query, {
            "session_id": self._session_id,
            "limit": self._window * 2,
        })
        return messages_from_dict(results)

    @messages.setter
    def messages(self, messages: List[BaseMessage]) -> None:
        raise NotImplementedError(
            "Direct assignment to 'messages' is not allowed."
            " Use the 'add_message' method instead."
        )

    def add_message(self, message: BaseMessage) -> None:
        self._graph.db.collection(self._collection).insert({
            "session_id": self._session_id,
            "role": message.type,
            "content": message.content,
            "timestamp": self._graph.db.datetime().isoformat(),  # optional
        })

    def clear(self, delete_session_node: bool = False) -> None:
        if delete_session_node:
            query = f"""
            FOR doc IN {self._collection}
                FILTER doc.session_id == @session_id
                REMOVE doc IN {self._collection}
            """
        else:
            query = f"""
            FOR doc IN {self._collection}
                FILTER doc.session_id == @session_id
                REMOVE doc IN {self._collection}
            """
        self._graph.run_aql(query, {"session_id": self._session_id})

    def __del__(self) -> None:
        pass
