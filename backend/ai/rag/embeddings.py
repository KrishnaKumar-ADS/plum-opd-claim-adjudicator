"""BGE embedding generation."""

from typing import Optional
from backend.utils.logger import get_logger

logger = get_logger("embeddings")

_model = None


def get_embedding_model():
    """Lazy-load the sentence-transformer embedding model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading BGE embedding model...")
            _model = SentenceTransformer("BAAI/bge-small-en-v1.5")
            logger.info("BGE embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    return _model


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts using BGE-small."""
    if not texts:
        return []

    model = get_embedding_model()

    # BGE models recommend prepending "Represent this sentence: " for better results
    prefixed_texts = [f"Represent this sentence: {t}" for t in texts]

    embeddings = model.encode(prefixed_texts, normalize_embeddings=True)
    return embeddings.tolist()


def generate_query_embedding(query: str) -> list[float]:
    """Generate embedding for a single query."""
    model = get_embedding_model()

    # BGE recommends different prefix for queries
    prefixed = f"Represent this sentence for searching relevant passages: {query}"

    embedding = model.encode([prefixed], normalize_embeddings=True)
    return embedding[0].tolist()
