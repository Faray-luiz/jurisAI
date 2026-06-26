import os
import requests
from typing import List, Dict, Any

# Pre-defined domains to search or restrict to
TRUSTED_DOMAINS = [
    "planalto.gov.br",
    "stf.jus.br",
    "stj.jus.br",
    "jusbrasil.com.br",
    "conjur.com.br",
    "lexml.gov.br"
]

MOCK_SEARCH_RESULTS = [
    {
        "title": "Súmula Vinculante 57 do STF - Imunidade Tributária de Livros Eletrônicos",
        "snippet": "A Súmula Vinculante 57 do STF estabelece: 'A imunidade tributária recíproca prevista no art. 150, VI, a, da CF/88 sobre livros, periódicos e o papel destinado a sua impressão aplica-se aos e-readers e livros digitais.'",
        "link": "https://portal.stf.jus.br/jurisprudencia/sumulas/sumula_vinculante_57",
        "source": "STF"
    },
    {
        "title": "Artigo 186 do Código Civil - Ato Ilícito Civil",
        "snippet": "O Artigo 186 do Código Civil consagra a regra geral de responsabilidade civil extracontratual por ato ilícito: 'Aquele que, por ação ou omissão voluntária, negligência ou imprudência, violar direito e causar dano a outrem, comete ato ilícito.'",
        "link": "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm#art186",
        "source": "Planalto"
    },
    {
        "title": "Jurisprudência STJ - Recurso Especial REsp 1.234.567/SP (Dever de Indenizar)",
        "snippet": "RECURSO ESPECIAL. CIVIL. RESPONSABILIDADE CIVIL. CONTRATO DE PROMESSA DE COMPRA E VENDA. ATRASO NA ENTREGA DE IMÓVEL. Caracterizado o dever de indenizar por lucros cessantes presumidos em virtude de atraso de obra sob o Art. 927 do CC.",
        "link": "https://processo.stj.jus.br/processo/pesquisa/?num_processo=1234567",
        "source": "STJ"
    },
    {
        "title": "Responsabilidade Civil por Atraso de Obra e Danos Morais - Jusbrasil",
        "snippet": "A jurisprudência do STJ e dos Tribunais de Justiça estaduais é pacífica no sentido de que o atraso injustificado na entrega de imóvel gera dever de indenizar por danos morais e lucros cessantes configurando negligência da construtora.",
        "link": "https://www.jusbrasil.com.br/jurisprudencia/busca?q=atraso+entrega+imovel",
        "source": "Jusbrasil"
    }
]

def search_web_juridico(query: str) -> List[Dict[str, Any]]:
    """
    Searches the internet for legal documents, restricting query to trusted domains.
    Falls back to high-fidelity mock results if no API key is configured.
    """
    tavily_key = os.getenv("TAVILY_API_KEY")
    serper_key = os.getenv("SERPER_API_KEY")
    
    # Restrict query to our trusted domains
    domain_filter = " OR ".join([f"site:{d}" for d in TRUSTED_DOMAINS])
    restricted_query = f"({query}) ({domain_filter})"
    
    # 1. Try Tavily Search API
    if tavily_key and tavily_key != "mock-tavily-key":
        try:
            url = "https://api.tavily.com/search"
            payload = {
                "api_key": tavily_key,
                "query": query,
                "include_domains": TRUSTED_DOMAINS,
                "max_results": 4
            }
            response = requests.post(url, json=payload, timeout=5)
            if response.status_code == 200:
                results = response.json().get("results", [])
                formatted = []
                for r in results:
                    source = "Web"
                    for d in TRUSTED_DOMAINS:
                        if d in r.get("url", "").lower():
                            source = d.split(".")[0].upper()
                            break
                    formatted.append({
                        "title": r.get("title", "Documento Jurídico"),
                        "snippet": r.get("content", ""),
                        "link": r.get("url", ""),
                        "source": source
                    })
                return formatted
        except Exception as e:
            print(f"[Search Warning] Tavily query failed: {e}. Trying fallback.")
            
    # 2. Try Serper Search API
    if serper_key and serper_key != "mock-serper-key":
        try:
            url = "https://google.serper.dev/search"
            headers = {
                "X-API-KEY": serper_key,
                "Content-Type": "application/json"
            }
            payload = {
                "q": restricted_query,
                "num": 4
            }
            response = requests.post(url, json=payload, headers=headers, timeout=5)
            if response.status_code == 200:
                results = response.json().get("organic", [])
                formatted = []
                for r in results:
                    source = "Web"
                    for d in TRUSTED_DOMAINS:
                        if d in r.get("link", "").lower():
                            source = d.split(".")[0].upper()
                            break
                    formatted.append({
                        "title": r.get("title", "Documento Jurídico"),
                        "snippet": r.get("snippet", ""),
                        "link": r.get("link", ""),
                        "source": source
                    })
                return formatted
        except Exception as e:
            print(f"[Search Warning] Serper query failed: {e}. Trying fallback.")

    # 3. Fallback/Mock Mode (Simulation)
    # Perform a simple keyword-based search over our high-fidelity mocks
    query_words = set(query.lower().split())
    matched = []
    
    for r in MOCK_SEARCH_RESULTS:
        text_to_search = (r["title"] + " " + r["snippet"]).lower()
        match_score = sum(1 for w in query_words if w in text_to_search)
        if match_score > 0:
            matched.append((r, match_score))
            
    if matched:
        matched.sort(key=lambda x: x[1], reverse=True)
        return [item[0] for item in matched[:4]]
        
    return MOCK_SEARCH_RESULTS[:3]
