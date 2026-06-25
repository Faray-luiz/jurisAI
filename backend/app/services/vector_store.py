import re
import json
import math
from typing import List, Dict, Any, Optional
from backend.app.core.config import settings

# ---------------------------------------------------------------------------
# Vector Embedding and Cosine Similarity Helpers
# ---------------------------------------------------------------------------

def generate_embedding(text: str) -> List[float]:
    """
    Generates a 1536-dimensional vector embedding for the given text.
    Calls the real OpenAI API if the key is configured, otherwise falls back
    to a deterministic mock embedding vector for development stability.
    """
    is_openai_mock = settings.OPENAI_API_KEY == "mock-openai-key" or not settings.OPENAI_API_KEY
    
    if is_openai_mock:
        # Generate a deterministic pseudo-random embedding vector
        import random
        h = hash(text)
        random.seed(h)
        vector = [random.uniform(-1.0, 1.0) for _ in range(1536)]
        # Normalize vector to unit length
        mag = sum(x*x for x in vector)**0.5
        if mag > 0:
            vector = [x/mag for x in vector]
        return vector
        
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.embeddings.create(
            input=[text],
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"[Embedding Error] Calling OpenAI failed: {e}. Falling back to mock vector.")
        import random
        random.seed(hash(text))
        vector = [random.uniform(-1.0, 1.0) for _ in range(1536)]
        mag = sum(x*x for x in vector)**0.5
        if mag > 0:
            vector = [x/mag for x in vector]
        return vector

def dot_product(v1: List[float], v2: List[float]) -> float:
    return sum(x * y for x, y in zip(v1, v2))

def magnitude(v: List[float]) -> float:
    return math.sqrt(sum(x * x for x in v))

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    mag1 = magnitude(v1)
    mag2 = magnitude(v2)
    if not mag1 or not mag2:
        return 0.0
    return dot_product(v1, v2) / (mag1 * mag2)

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
    threshold: float = 0.15
) -> List[Dict[str, Any]]:
    """
    Performs a real semantic similarity search (Cosine Similarity of Embeddings)
    over the grounding document corpus.
    """
    from backend.app.db.session import SessionLocal
    from backend.app.db.models import DBGroundingDoc
    from sqlalchemy import or_
    import json

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
            docs = (
                db.query(DBGroundingDoc)
                .filter(DBGroundingDoc.is_active == True)
                .all()
            )
            
        if not docs:
            return []

        # Check if we are running in simulation/mock mode
        is_openai_mock = settings.OPENAI_API_KEY == "mock-openai-key" or not settings.OPENAI_API_KEY
        
        scored = []
        if is_openai_mock:
            # Fall back to high-fidelity hybrid Jaccard-based scoring in mock/simulation mode
            for doc in docs:
                score = compute_hybrid_score(query, doc.text, doc.citation)
                # Keep a slightly higher threshold for mock Jaccard queries as in legacy (0.18)
                mock_threshold = max(threshold, 0.18)
                if score >= mock_threshold:
                    scored.append({
                        "citation": doc.citation,
                        "text": doc.text,
                        "source": doc.source,
                        "score": round(score, 4),
                        "agent_task_type": doc.agent_task_type or "global"
                    })
        else:
            # Real mode: Cosine Similarity of Embeddings
            query_embedding = generate_embedding(query)
            for doc in docs:
                # Lazy-load/compute document embedding if missing
                doc_embedding = None
                if doc.embedding_json:
                    try:
                        doc_embedding = json.loads(doc.embedding_json)
                    except Exception:
                        pass
                        
                if not doc_embedding:
                    # Generate and persist the embedding in the database
                    doc_embedding = generate_embedding(doc.text)
                    doc.embedding_json = json.dumps(doc_embedding)
                    db.add(doc)
                    db.commit() # Save the generated embedding for future queries!
                    
                # Compute cosine similarity
                score = cosine_similarity(query_embedding, doc_embedding)
                
                # Precision boost if the article numbers match exactly
                query_digits = extract_article_numbers(query)
                citation_digits = extract_article_numbers(doc.citation)
                if query_digits and citation_digits and query_digits & citation_digits:
                    score += 0.10 # Add precision boost for exact article number matches!
                elif query_digits and citation_digits and not query_digits & citation_digits:
                    # Hard filter: if query mentions specific article numbers but they don't
                    # appear in this citation, reduce score to 0 to prevent false matches
                    score = 0.0

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
    finally:
        db.close()


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
