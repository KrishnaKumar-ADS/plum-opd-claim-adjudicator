"""RAG retrieval logic."""

from backend.ai.rag.embeddings import generate_query_embedding
from backend.ai.rag.vectordb import query_documents
from backend.utils.logger import get_logger

logger = get_logger("retriever")


_local_chunks_cache = None

def _get_local_chunks():
    global _local_chunks_cache
    if _local_chunks_cache is not None:
        return _local_chunks_cache

    from backend.utils.parsers import chunk_text, load_json_file, load_text_file
    from backend.config import get_settings
    
    settings = get_settings()
    chunks = []

    # Load policy terms
    policy_path = settings.policy_terms_path
    if policy_path.exists():
        try:
            policy = load_json_file(policy_path)
            # Coverage details
            coverage = policy.get("coverage_details", {})
            for category, details in coverage.items():
                if isinstance(details, dict):
                    text = f"Coverage Category: {category}\n"
                    for key, value in details.items():
                        text += f"  {key}: {value}\n"
                    chunks.append((text, {"source": "policy_terms", "section": f"coverage_{category}"}))
                else:
                    chunks.append((f"Coverage: {category} = {details}", {"source": "policy_terms", "section": f"coverage_{category}"}))
            
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
            chunks.append((text, {"source": "policy_terms", "section": "waiting_periods"}))

            # Exclusions
            exclusions = policy.get("exclusions", [])
            text = "Policy Exclusions (NOT covered):\n" + "\n".join(f"  - {e}" for e in exclusions)
            chunks.append((text, {"source": "policy_terms", "section": "exclusions"}))

            # Claim requirements
            requirements = policy.get("claim_requirements", {})
            text = "Claim Requirements:\n"
            for key, value in requirements.items():
                if isinstance(value, list):
                    text += f"  {key}:\n" + "\n".join(f"    - {v}" for v in value) + "\n"
                else:
                    text += f"  {key}: {value}\n"
            chunks.append((text, {"source": "policy_terms", "section": "claim_requirements"}))

            # Network hospitals
            network = policy.get("network_hospitals", [])
            text = "Network Hospitals:\n" + "\n".join(f"  - {h}" for h in network)
            chunks.append((text, {"source": "policy_terms", "section": "network_hospitals"}))

            # Cashless facilities
            cashless = policy.get("cashless_facilities", {})
            text = "Cashless Facilities:\n"
            for key, value in cashless.items():
                text += f"  {key}: {value}\n"
            chunks.append((text, {"source": "policy_terms", "section": "cashless_facilities"}))
        except Exception as e:
            logger.warning(f"Failed to load policy terms for local chunks: {e}")

    # Load adjudication rules
    rules_path = settings.adjudication_rules_path
    if rules_path.exists():
        try:
            rules_text = load_text_file(rules_path)
            rules_chunks = chunk_text(rules_text, chunk_size=300, overlap=30)
            for i, chunk in enumerate(rules_chunks):
                chunks.append((chunk, {"source": "adjudication_rules", "section": f"chunk_{i}"}))
        except Exception as e:
            logger.warning(f"Failed to load adjudication rules for local chunks: {e}")

    _local_chunks_cache = chunks
    return chunks


def retrieve_relevant_context(query: str, n_results: int = 5) -> str:
    """
    Retrieve relevant policy/rules context for a given claim query.
    Returns concatenated relevant text passages.
    """
    try:
        # 1. Normalize query and extract keywords
        import re
        query_clean = query.lower()
        words = re.findall(r'[a-z0-9]{3,}', query_clean)
        
        # Stopwords to filter out
        stopwords = {"the", "and", "for", "with", "are", "what", "policy", "terms", "condition", "treatment", "requirements", "about", "how", "why"}
        keywords = [w for w in words if w not in stopwords]
        
        if not keywords:
            keywords = words if words else [query_clean]

        # 2. Get local chunks and calculate match score
        local_chunks = _get_local_chunks()
        scored_chunks = []
        
        for chunk, meta in local_chunks:
            chunk_lower = chunk.lower()
            score = 0
            for kw in keywords:
                count = chunk_lower.count(kw)
                if count > 0:
                    sec_weight = 3 if kw in meta.get("section", "").lower() or kw in meta.get("source", "").lower() else 1
                    score += count * sec_weight
            
            if score > 0:
                scored_chunks.append((score, chunk, meta))
                
        # Sort by score descending
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        
        if scored_chunks:
            top_chunks = scored_chunks[:n_results]
            context_parts = []
            for idx, (score, chunk, meta) in enumerate(top_chunks):
                source = meta.get("source", "unknown")
                section = meta.get("section", "")
                relevance = round(min(1.0, 0.5 + (score / 100)), 3)
                context_parts.append(
                    f"[Source: {source} | Section: {section} | Relevance: {relevance}]\n{chunk}"
                )
            context = "\n\n---\n\n".join(context_parts)
            logger.info(f"Local keyword retrieval successful: {len(top_chunks)} passages found in <1ms (score range: {top_chunks[0][0]}-{top_chunks[-1][0]})")
            return context

        # 3. Fallback to vector search if keyword search returned nothing
        import os
        if os.environ.get("VERCEL"):
            logger.warning("Vector search fallback disabled on Vercel environment to prevent timeouts/OOM")
            return ""

        logger.info("Local keyword matching yielded zero results. Falling back to vector search...")
        query_embedding = generate_query_embedding(query)
        results = query_documents(query_embedding, n_results=n_results)

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        if not documents:
            logger.warning("No relevant documents found for query in vector search fallback")
            return ""

        context_parts = []
        for doc, meta, dist in zip(documents, metadatas, distances):
            source = meta.get("source", "unknown")
            section = meta.get("section", "")
            relevance = round(1 - dist, 3)
            context_parts.append(
                f"[Source: {source} | Section: {section} | Relevance: {relevance}]\n{doc}"
            )

        context = "\n\n---\n\n".join(context_parts)
        logger.info(f"Vector retrieval successful: {len(documents)} passages found")
        return context

    except Exception as e:
        logger.error(f"RAG retrieval failed: {e}")
        return ""


def retrieve_coverage_context(treatment_type: str, diagnosis: str) -> str:
    """Retrieve coverage-specific context for a treatment and diagnosis."""
    query = (
        f"Coverage and policy terms for treatment: {treatment_type}. "
        f"Diagnosis: {diagnosis}. "
        f"What are the limits, exclusions, copay, and sub-limits?"
    )
    return retrieve_relevant_context(query, n_results=4)


def retrieve_eligibility_context(condition: str) -> str:
    """Retrieve eligibility-related context including waiting periods."""
    query = (
        f"Eligibility requirements and waiting periods for condition: {condition}. "
        f"What are the waiting periods for pre-existing diseases?"
    )
    return retrieve_relevant_context(query, n_results=3)


def retrieve_exclusions_context(treatment: str) -> str:
    """Retrieve exclusions context to check if treatment is excluded."""
    query = (
        f"Policy exclusions list. Is {treatment} excluded from coverage? "
        f"What treatments are not covered under the policy?"
    )
    return retrieve_relevant_context(query, n_results=3)
