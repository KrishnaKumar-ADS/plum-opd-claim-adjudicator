"""Build Chroma vector database from policy documents."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.ai.rag.ingest import ingest_policy_documents


def main():
    print("Building vector store...")
    ingest_policy_documents(force_rebuild=True)
    print("Vector store built successfully!")


if __name__ == "__main__":
    main()
