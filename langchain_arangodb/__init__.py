from importlib import metadata

from langchain_arangodb.chains.graph_qa.aql import GraphAQLQAChain
from langchain_arangodb.chat_message_histories.arangodb import ArangoChatMessageHistory
from langchain_arangodb.graphs.arango_graph import ArangoGraph
from langchain_arangodb.vectorstores.arango_vector import ArangoVector

try:
    __version__ = metadata.version(__package__)
except metadata.PackageNotFoundError:
    # Case where package metadata is not available.
    __version__ = ""
del metadata  # optional, avoids polluting the results of dir(__package__)

__all__ = [
    "GraphAQLQAChain",
    "ArangoChatMessageHistory",
    "ArangoGraph",
    "ArangoVector",
    "__version__",
]
