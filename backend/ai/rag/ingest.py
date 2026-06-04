"""Policy document ingestion."""

import json
from pathlib import Path
from backend.config import get_settings
from backend.utils.parsers import chunk_text, load_json_file, load_text_file
from backend.ai.rag.embeddings import generate_embeddings
from backend.ai.rag.vectordb import add_documents, reset_collection, get_collection
from backend.utils.logger import get_logger

logger = get_logger("ingest")
settings = get_settings()


def ingest_policy_documents(force_rebuild: bool = False):
    """
    Ingest policy terms and adjudication rules into the vector store.
    Skips if documents already exist unless force_rebuild is True.
    """
    if force_rebuild:
        logger.info("Force rebuilding vector store...")
        reset_collection()
    else:
        collection = get_collection()
        if collection.count() > 0:
            logger.info(f"Vector store already has {collection.count()} documents. Skipping ingestion.")
            return

    all_chunks = []
    all_metadatas = []
    all_ids = []

    # 1. Ingest policy_terms.json
    policy_path = settings.policy_terms_path
    if policy_path.exists():
        policy_chunks, policy_meta = _process_policy_terms(policy_path)
        for i, (chunk, meta) in enumerate(zip(policy_chunks, policy_meta)):
            all_chunks.append(chunk)
            all_metadatas.append(meta)
            all_ids.append(f"policy_{i}")
        logger.info(f"Processed {len(policy_chunks)} chunks from policy_terms.json")
    else:
        logger.warning(f"Policy terms file not found: {policy_path}")

    # 2. Ingest adjudication_rules.md
    rules_path = settings.adjudication_rules_path
    if rules_path.exists():
        rules_text = load_text_file(rules_path)
        rules_chunks = chunk_text(rules_text, chunk_size=300, overlap=30)
        for i, chunk in enumerate(rules_chunks):
            all_chunks.append(chunk)
            all_metadatas.append({"source": "adjudication_rules", "section": f"chunk_{i}"})
            all_ids.append(f"rules_{i}")
        logger.info(f"Processed {len(rules_chunks)} chunks from adjudication_rules.md")
    else:
        logger.warning(f"Adjudication rules file not found: {rules_path}")

    # 3. Generate embeddings and store
    if all_chunks:
        logger.info(f"Generating embeddings for {len(all_chunks)} chunks...")
        embeddings = generate_embeddings(all_chunks)
        add_documents(
            documents=all_chunks,
            embeddings=embeddings,
            metadatas=all_metadatas,
            ids=all_ids,
        )
        logger.info(f"Successfully ingested {len(all_chunks)} documents into vector store")
    else:
        logger.warning("No documents to ingest")


def _process_policy_terms(filepath: Path) -> tuple[list[str], list[dict]]:
    """Process policy_terms.json into text chunks with metadata."""
    policy = load_json_file(filepath)
    chunks = []
    metadatas = []

    # Coverage details — one chunk per category
    coverage = policy.get("coverage_details", {})
    for category, details in coverage.items():
        if isinstance(details, dict):
            text = f"Coverage Category: {category}\n"
            for key, value in details.items():
                text += f"  {key}: {value}\n"
            chunks.append(text)
            metadatas.append({"source": "policy_terms", "section": f"coverage_{category}"})
        else:
            chunks.append(f"Coverage: {category} = {details}")
            metadatas.append({"source": "policy_terms", "section": f"coverage_{category}"})

    # Waiting periods
    waiting = policy.get("waiting_periods", {})
    text = "Waiting Periods:\n"
    for key, value in waiting.items():
        if isinstance(value, dict):
            text += f"  {key}:\n"
            for k, v in value.items():
                text += f"    {k}: {v} days\n"
        else:
            text += f"  {key}: {value} days\n"
    chunks.append(text)
    metadatas.append({"source": "policy_terms", "section": "waiting_periods"})

    # Exclusions
    exclusions = policy.get("exclusions", [])
    text = "Policy Exclusions (NOT covered):\n" + "\n".join(f"  - {e}" for e in exclusions)
    chunks.append(text)
    metadatas.append({"source": "policy_terms", "section": "exclusions"})

    # Claim requirements
    requirements = policy.get("claim_requirements", {})
    text = "Claim Requirements:\n"
    for key, value in requirements.items():
        if isinstance(value, list):
            text += f"  {key}:\n" + "\n".join(f"    - {v}" for v in value) + "\n"
        else:
            text += f"  {key}: {value}\n"
    chunks.append(text)
    metadatas.append({"source": "policy_terms", "section": "claim_requirements"})

    # Network hospitals
    network = policy.get("network_hospitals", [])
    text = "Network Hospitals:\n" + "\n".join(f"  - {h}" for h in network)
    chunks.append(text)
    metadatas.append({"source": "policy_terms", "section": "network_hospitals"})

    # Cashless facilities
    cashless = policy.get("cashless_facilities", {})
    text = "Cashless Facilities:\n"
    for key, value in cashless.items():
        text += f"  {key}: {value}\n"
    chunks.append(text)
    metadatas.append({"source": "policy_terms", "section": "cashless_facilities"})

    return chunks, metadatas
