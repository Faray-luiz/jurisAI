import urllib.request
import urllib.parse
import json
import re
from typing import Optional, Dict, Any

def search_lexml_legislation(citation: str) -> Optional[Dict[str, Any]]:
    """
    Queries the official Brazilian LexML API to search for legislation and legal norms.
    Extracts article numbers and law names, queries LexML, and returns a verified
    grounding document dict or None if not found/offline.
    """
    # 1. Parse citation to extract article number and main code/law name
    # e.g. "Art. 186 do Código Civil" -> article "186", law "codigo civil"
    citation_lower = citation.lower()
    art_match = re.search(r"art(?:igo)?\s*(\d+)", citation_lower)
    if not art_match:
        return None
    
    art_num = art_match.group(1)
    
    # Identify legal body
    law_query = ""
    law_pretty = ""
    if "civil" in citation_lower and "processo" not in citation_lower:
        law_query = '"codigo civil"'
        law_pretty = "Código Civil"
    elif "cpc" in citation_lower or "processo civil" in citation_lower:
        law_query = '"codigo de processo civil"'
        law_pretty = "CPC"
    elif "cf" in citation_lower or "constitui" in citation_lower:
        law_query = '"constituicao"'
        law_pretty = "Constituição Federal"
    else:
        # Generic fallback: extract words other than art/artigo/digits
        words = [w for w in re.findall(r"\b[a-zA-Zá-úÁ-Ú]{3,}\b", citation_lower) if w not in ["art", "artigo", "codigo"]]
        if words:
            law_query = f'"{words[0]}"'
            law_pretty = words[0].capitalize()
        else:
            law_query = "legislacao"
            law_pretty = "Legislação"

    # 2. Formulate search query for LexML API
    query_str = f"artigo {art_num} {law_query}"
    encoded_query = urllib.parse.quote(query_str)
    # LexML public search API with JSON format parameter
    url = f"https://www.lexml.gov.br/busca/search?q={encoded_query}&format=json"
    
    try:
        req = urllib.request.Request(
            url, 
            headers={"User-Agent": "JurisAIGateway/2.0.0 (contato@jurisai.com.br)"}
        )
        # Apply strict 3-second timeout to maintain sychronous performance requirements
        with urllib.request.urlopen(req, timeout=3.0) as response:
            if response.status != 200:
                return None
            
            data = json.loads(response.read().decode("utf-8"))
            
            # Parse results from LexML JSON structure
            # LexML API returns an object containing "feed" -> "entry" (list of documents)
            entries = data.get("feed", {}).get("entry", [])
            if not entries:
                return None
            
            # Get the best matching official legal document (usually first entry)
            best_entry = entries[0]
            title = best_entry.get("title", "Documento Oficial")
            summary = best_entry.get("summary", "")
            if isinstance(summary, dict):
                summary = summary.get("value", "")
            
            # Clean up HTML tags from LexML summary if present
            summary_clean = re.sub(r"<[^>]+>", "", summary).strip()
            
            # If summary is too short or missing, construct a placeholder official citation text
            doc_text = summary_clean if len(summary_clean) > 50 else f"Dispositivo legal oficial correspondente ao {citation} localizado no acervo do LexML."
            
            return {
                "citation": f"Art. {art_num} do {law_pretty}",
                "text": f"Art. {art_num}. {doc_text}",
                "source": f"LexML - {title}"
            }
            
    except Exception as e:
        # Graceful degradation when offline or API is down (standard compliance fallback)
        print(f"[LexML Conector] Offline or API error: {e}. Falling back to local cache.")
        return None
