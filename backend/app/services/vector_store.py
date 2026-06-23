import re
from typing import List, Dict, Any

def tokenize(text: str) -> set:
    """
    Tokenizes and normalizes text for comparison.
    """
    text_clean = re.sub(r'[^\w\s]', '', text.lower())
    # Remove common stop words to improve keyword match accuracy
    stop_words = {"da", "do", "de", "o", "a", "em", "um", "uma", "para", "com", "se"}
    tokens = [w for w in text_clean.split() if w not in stop_words]
    return set(tokens)

def compute_similarity(query: str, document: str) -> float:
    """
    Computes Jaccard similarity coefficient between query and document.
    """
    query_tokens = tokenize(query)
    doc_tokens = tokenize(document)
    if not query_tokens or not doc_tokens:
        return 0.0
    intersection = query_tokens.intersection(doc_tokens)
    union = query_tokens.union(doc_tokens)
    return len(intersection) / len(union)

def query_vector_store(query: str) -> Dict[str, Any]:
    """
    Performs a simulated vector store semantic query.
    Compares the query against the grounding legislation corpus.
    """
    from backend.app.db.session import SessionLocal
    from backend.app.db.models import DBGroundingDoc
    
    db = SessionLocal()
    try:
        grounding_docs = db.query(DBGroundingDoc).filter(DBGroundingDoc.is_active == True).all()
    finally:
        db.close()
        
    best_match = None
    best_score = 0.0
    
    # Extract digits to prevent matching wrong articles (e.g. Art. 999 vs Art. 319)
    query_digits = set(re.findall(r"\d+", query))
    
    for doc in grounding_docs:
        doc_digits = set(re.findall(r"\d+", doc.citation))
        
        # If numbers are present in both but don't match, force score to 0
        if query_digits and doc_digits and not query_digits.intersection(doc_digits):
            continue
            
        score_text = compute_similarity(query, doc.text)
        score_citation = compute_similarity(query, doc.citation)
        
        # Boost if the citation code matches directly
        score = max(score_text, score_citation * 1.8)
        
        if score > best_score:
            best_score = score
            best_match = {
                "citation": doc.citation,
                "text": doc.text,
                "source": doc.source
            }
            
    # We require a threshold of 0.20 to confirm a match
    if best_score >= 0.20 and best_match:
        return {
            "match": True,
            "score": best_score,
            "data": best_match
        }
        
    return {
        "match": False,
        "score": best_score,
        "data": None
    }
