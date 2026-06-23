import re
from typing import List, Dict, Any, Optional

# ---------------------------------------------------------------------------
# Text Processing Helpers
# ---------------------------------------------------------------------------

# Portuguese legal stop-words — stripped from queries/documents before scoring
_STOP_WORDS = {
    "da", "do", "de", "o", "a", "em", "um", "uma", "para", "com", "se",
    "que", "no", "na", "ao", "os", "as", "dos", "das", "pelo", "pela",
    "por", "mais", "ou", "quando", "então", "cada", "foi", "ser"
}

# Legal domain keywords that should receive a relevance bonus when matched
_LEGAL_BOOST_TERMS = {
    "artigo", "art", "lei", "código", "constituição", "decreto", "resolução",
    "ônus", "prova", "petição", "inicial", "recurso", "indenização", "ilícito",
    "civil", "processo", "processual", "responsabilidade", "nexo", "dano"
}


def tokenize(text: str) -> set:
    """Tokenizes and normalizes Portuguese legal text."""
    text_clean = re.sub(r'[^\w\s]', '', text.lower())
    tokens = [w for w in text_clean.split() if w not in _STOP_WORDS and len(w) > 1]
    return set(tokens)


def extract_article_numbers(text: str) -> set:
    """Extracts article/law numbers (e.g. '186', '319') from any text."""
    return set(re.findall(r'\d+', text))


def compute_jaccard(query: str, document: str) -> float:
    """Standard Jaccard similarity between query and document token sets."""
    q_tokens = tokenize(query)
    d_tokens = tokenize(document)
    if not q_tokens or not d_tokens:
        return 0.0
    intersection = q_tokens & d_tokens
    union = q_tokens | d_tokens
    return len(intersection) / len(union)


def compute_legal_boost(query_tokens: set, citation: str) -> float:
    """
    Computes a bonus score when the query tokens overlap with legal domain
    boost terms found in the citation label (e.g. 'art', 'código', 'cpc').
    """
    citation_tokens = tokenize(citation)
    overlap = query_tokens & _LEGAL_BOOST_TERMS & citation_tokens
    return 0.05 * len(overlap)


def compute_hybrid_score(query: str, doc_text: str, doc_citation: str) -> float:
    """
    Hybrid similarity combining:
      - Jaccard on full text (body content)
      - Jaccard on citation label (weighted heavily — most discriminating field)
      - Article number exact matching (bonus on numeric precision)
      - Legal domain keyword boost

    Returns a single float score in [0, ∞).
    """
    query_digits = extract_article_numbers(query)
    citation_digits = extract_article_numbers(doc_citation)

    # Hard filter: if query mentions specific article numbers but they don't
    # appear in the citation, discard to prevent false matches (e.g. Art.186 ≠ Art.319)
    if query_digits and citation_digits and not query_digits & citation_digits:
        return 0.0

    score_text = compute_jaccard(query, doc_text)
    score_citation = compute_jaccard(query, doc_citation)

    # Citation match is weighted more heavily (1.8×) as it is the most precise field
    combined = max(score_text, score_citation * 1.8)

    # Add legal domain keyword bonus
    combined += compute_legal_boost(tokenize(query), doc_citation)

    # Bonus when article numbers match exactly (highly reliable signal)
    if query_digits and citation_digits and query_digits & citation_digits:
        combined += 0.15

    return combined


# ---------------------------------------------------------------------------
# Main RAG Query Function — Mission-Aware Top-K Retrieval
# ---------------------------------------------------------------------------

def query_vector_store(
    query: str,
    task_type: str = "default",
    top_k: int = 3,
    threshold: float = 0.18
) -> List[Dict[str, Any]]:
    """
    Performs a mission-aware semantic similarity search over the grounding
    document corpus and returns up to `top_k` ranked results.

    Strategy:
      1. Filter documents by mission: load only docs tagged with the active
         agent task_type OR tagged as "global" (cross-mission knowledge).
      2. Score each document with the hybrid similarity function.
      3. Return the top_k results that exceed the minimum threshold.

    Args:
        query:     The user's natural language input text.
        task_type: The active agent mission (e.g. "analise_peticao",
                   "rascunho_recurso", "default"). Defaults to "default".
        top_k:     Maximum number of documents to return.
        threshold: Minimum similarity score to be considered a match.

    Returns:
        List of dicts with keys: citation, text, source, score, agent_task_type.
    """
    from backend.app.db.session import SessionLocal
    from backend.app.db.models import DBGroundingDoc
    from sqlalchemy import or_

    db = SessionLocal()
    try:
        # Normalize task_type aliases
        normalized = task_type if task_type in ("analise_peticao", "rascunho_recurso") else None

        # Load mission-specific docs + always-available global docs
        if normalized:
            docs = (
                db.query(DBGroundingDoc)
                .filter(
                    DBGroundingDoc.is_active == True,
                    or_(
                        DBGroundingDoc.agent_task_type == normalized,
                        DBGroundingDoc.agent_task_type == "global",
                        DBGroundingDoc.agent_task_type == None,
                    )
                )
                .all()
            )
        else:
            # For "default" or unknown missions, load everything active
            docs = (
                db.query(DBGroundingDoc)
                .filter(DBGroundingDoc.is_active == True)
                .all()
            )
    finally:
        db.close()

    if not docs:
        return []

    # Score all candidate documents
    scored = []
    for doc in docs:
        score = compute_hybrid_score(query, doc.text, doc.citation)
        if score >= threshold:
            scored.append({
                "citation": doc.citation,
                "text": doc.text,
                "source": doc.source,
                "score": round(score, 4),
                "agent_task_type": doc.agent_task_type or "global"
            })

    # Sort descending by score and return top_k
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


# ---------------------------------------------------------------------------
# Legacy single-match wrapper (kept for backwards compatibility with grounding.py)
# ---------------------------------------------------------------------------

def query_vector_store_single(query: str) -> Dict[str, Any]:
    """
    Legacy wrapper returning a single best-match result dict for the grounding
    citation verification service. Searches the full corpus (no mission filter).
    """
    results = query_vector_store(query=query, task_type="default", top_k=1, threshold=0.20)
    if results:
        return {"match": True, "score": results[0]["score"], "data": results[0]}
    return {"match": False, "score": 0.0, "data": None}
