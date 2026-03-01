"""
HALO Health – ChromaDB Vector Store Service
One persistent ChromaDB client; one collection per agent type.
"""
import logging
from typing import List, Dict, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

# Prevent PostHog capture errors due to version mismatch or missing posthog module.
# ChromaDB's internal fallback has a bug where capture() takes 1 argument instead of 3.
import sys
class DummyPosthog:
    def __init__(self, *args, **kwargs):
        pass
    def capture(self, *args, **kwargs):
        pass
class DummyPosthogModule:
    def __init__(self):
        self.Posthog = DummyPosthog
    def capture(self, *args, **kwargs):
        pass

sys.modules['posthog'] = DummyPosthogModule()

from backend.config import settings

logger = logging.getLogger(__name__)

_client: Optional[chromadb.PersistentClient] = None


def _get_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=settings.chroma_db_path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client


def _collection_name(agent_type: str, user_id: int) -> str:
    return f"{agent_type}__user_{user_id}"


def add_to_memory(
    agent_type: str,
    user_id: int,
    doc_id: str,
    text: str,
    metadata: Optional[Dict] = None,
) -> None:
    """Add a document to the agent's per-user collection."""
    try:
        col = _get_client().get_or_create_collection(
            name=_collection_name(agent_type, user_id)
        )
        col.upsert(
            ids=[doc_id],
            documents=[text],
            metadatas=[metadata or {}],
        )
    except Exception as exc:
        logger.warning("ChromaDB add_to_memory failed: %s", exc)


def query_memory(
    agent_type: str,
    user_id: int,
    query: str,
    n_results: int = 5,
) -> List[str]:
    """Query the agent's per-user collection for relevant context."""
    try:
        col = _get_client().get_or_create_collection(
            name=_collection_name(agent_type, user_id)
        )
        results = col.query(query_texts=[query], n_results=n_results)
        return results.get("documents", [[]])[0]
    except Exception as exc:
        logger.warning("ChromaDB query_memory failed: %s", exc)
        return []
