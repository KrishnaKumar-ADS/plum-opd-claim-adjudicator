"""ChromaDB operations."""

import os
import shutil
import chromadb
from typing import Optional
from backend.config import get_settings
from backend.utils.logger import get_logger

logger = get_logger("vectordb")
settings = get_settings()

_chroma_client: Optional[chromadb.ClientAPI] = None
_collection = None

COLLECTION_NAME = "policy_documents"


def _reset_client_state():
    """Clear cached ChromaDB client and collection handles."""
    global _chroma_client, _collection
    _chroma_client = None
    _collection = None


def _wipe_persist_dir():
    """Remove a corrupted or stale ChromaDB persist directory."""
    persist_dir = settings.chroma_persist_dir
    if os.path.isdir(persist_dir):
        shutil.rmtree(persist_dir, ignore_errors=True)
    os.makedirs(persist_dir, exist_ok=True)
    logger.info(f"Wiped ChromaDB persist directory at {persist_dir}")


def get_chroma_client() -> chromadb.ClientAPI:
    """Get or create ChromaDB persistent client."""
    global _chroma_client
    if _chroma_client is None:
        os.makedirs(settings.chroma_persist_dir, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        logger.info(f"ChromaDB client initialized at {settings.chroma_persist_dir}")
    return _chroma_client


def get_collection():
    """Get or create the policy documents collection."""
    global _collection
    if _collection is not None:
        return _collection

    try:
        client = get_chroma_client()
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"Collection '{COLLECTION_NAME}' ready ({_collection.count()} docs)")
        return _collection
    except (KeyError, ValueError) as e:
        logger.warning(f"ChromaDB collection load failed ({e}); rebuilding vector store")
        _reset_client_state()
        _wipe_persist_dir()
        client = get_chroma_client()
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"Collection '{COLLECTION_NAME}' recreated ({_collection.count()} docs)")
        return _collection


def add_documents(
    documents: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict],
    ids: list[str],
):
    """Add documents with pre-computed embeddings to the collection."""
    collection = get_collection()

    collection.add(
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids,
    )

    logger.info(f"Added {len(documents)} documents to collection")


def query_documents(
    query_embedding: list[float],
    n_results: int = 5,
    where: Optional[dict] = None,
) -> dict:
    """Query the collection with a pre-computed embedding."""
    collection = get_collection()

    kwargs = {
        "query_embeddings": [query_embedding],
        "n_results": min(n_results, collection.count()) if collection.count() > 0 else 1,
    }
    if where:
        kwargs["where"] = where

    try:
        results = collection.query(**kwargs)
        logger.info(f"Query returned {len(results.get('documents', [[]])[0])} results")
        return results
    except Exception as e:
        logger.error(f"ChromaDB query failed: {e}")
        return {"documents": [[]], "metadatas": [[]], "distances": [[]]}


def reset_collection():
    """Delete and recreate the collection."""
    _reset_client_state()
    _wipe_persist_dir()
    logger.info(f"Collection '{COLLECTION_NAME}' reset")
    return get_collection()
