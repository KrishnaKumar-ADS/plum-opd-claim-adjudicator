"""Tests for RAG retrieval."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_ingest():
    from backend.ai.rag.ingest import ingest_policy_documents
    ingest_policy_documents(force_rebuild=True)
    from backend.ai.rag.vectordb import get_collection
    assert get_collection().count() > 0
    print("✅ RAG ingestion test passed")


def test_retrieval():
    from backend.ai.rag.retriever import retrieve_relevant_context
    context = retrieve_relevant_context("dental coverage limits")
    assert len(context) > 0
    print(f"✅ RAG retrieval test passed ({len(context)} chars)")


if __name__ == "__main__":
    test_ingest()
    test_retrieval()
