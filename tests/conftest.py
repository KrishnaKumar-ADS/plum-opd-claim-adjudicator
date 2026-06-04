"""Pytest configuration and mocks for tests."""
import sys
from unittest.mock import MagicMock

class MockSentenceTransformer:
    def __init__(self, model_name, *args, **kwargs):
        self.model_name = model_name

    def encode(self, sentences, *args, **kwargs):
        import numpy as np
        # Return dummy embeddings of 384 dimensions (matching BAAI/bge-small-en-v1.5)
        return np.ones((len(sentences), 384))

# Create a mock module for sentence_transformers to prevent downloading BGE from Hugging Face
mock_sentence_transformers = MagicMock()
mock_sentence_transformers.SentenceTransformer = MockSentenceTransformer

# Inject into sys.modules before any backend code imports sentence_transformers
sys.modules["sentence_transformers"] = mock_sentence_transformers
