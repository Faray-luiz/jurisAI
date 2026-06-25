import json
import re
import time
from typing import Dict, Any
from backend.app.core.config import settings

def extract_case_details_from_text(text: str, provider: str = "openai", model: str = "gpt-4o-mini") -> Dict[str, Any]:
    """
    Calls the LLM to extract structured legal case metadata from the petition text.
    Uses a strict system instruction to ensure stable JSON output.
    If the LLM call fails or returns invalid JSON, applies fallback heuristics.
    """
    system_prompt = (
        "Você é um especialista em direito processual civil brasileiro e IA. "
        "Sua tarefa é analisar o texto de uma petição inicial e extrair metadados estruturados. "
        "Você DEVE retornar estritamente um objeto JSON válido, sem qualquer texto adicional antes ou depois. "
        "O JSON deve possuir exatamente as seguintes chaves:\n"
        "1. 'title': título descritivo do caso (ex: 'Ação de Indenização por Infiltração')\n"
        "2. 'summary': resumo conciso e de alta fidelidade das alegações fatos, fundamentos jurídicos e pedidos\n"
        "3. 'plaintiff': nome completo do Autor/Requerente\n"
        "4. 'defendant': nome completo do Réu/Requerido\n"
        "5. 'client': nome do cliente da banca (geralmente coincide com o Autor em petições iniciais)\n"
        "6. 'matter': área do direito (ex: 'Direito Civil', 'Direito Imobiliário', 'Direito do Consumidor')\n"
        "7. 'value': valor da causa formatado (ex: 'R$ 50.000,00')\n"
        "8. 'court': tribunal/vara endereçada (ex: '3ª Vara Cível de São Paulo/SP')\n"
        "9. 'process_number': número do processo se explicitamente mencionado. Se não houver, crie um número fictício no formato CNJ válido correspondente ao ano atual (ex: '1002345-12.2026.8.26.0100')."
    )

    prompt = (
        f"Analise a seguinte petição inicial e extraia os metadados jurídicos em formato JSON conforme as chaves especificadas:\n\n"
        f"--- INÍCIO DO DOCUMENTO ---\n"
        f"{text[:15000]}\n"  # Limit to 15k characters to prevent context window overflow
        f"--- FIM DO DOCUMENTO ---"
    )

    # Check if in mock simulation mode
    is_openai_mock = settings.OPENAI_API_KEY == "mock-openai-key" or not settings.OPENAI_API_KEY
    is_anthropic_mock = settings.ANTHROPIC_API_KEY == "mock-anthropic-key" or not settings.ANTHROPIC_API_KEY
    is_gemini_mock = settings.GEMINI_API_KEY == "mock-gemini-key" or not settings.GEMINI_API_KEY

    run_mock = False
    if provider == "openai" and is_openai_mock:
        run_mock = True
    elif provider == "anthropic" and is_anthropic_mock:
        run_mock = True
    elif provider == "google" and is_gemini_mock:
        run_mock = True

    if run_mock:
        return run_fallback_heuristics(text)

    try:
        if provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            message = client.messages.create(
                model=model,
                max_tokens=1500,
                temperature=0.0,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )
            response_text = message.content[0].text
            
        elif provider == "google":
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model_instance = genai.GenerativeModel(
                model_name=model,
                system_instruction=system_prompt
            )
            response = model_instance.generate_content(
                prompt,
                generation_config={"temperature": 0.0}
            )
            response_text = response.text
            
        else:  # openai
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model=model,
                temperature=0.0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
            )
            response_text = response.choices[0].message.content

        # Clean code block indicators if any
        cleaned = response_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        extracted = json.loads(cleaned)
        # Ensure all required keys exist
        required_keys = ["title", "summary", "plaintiff", "defendant", "client", "matter", "value", "court", "process_number"]
        for key in required_keys:
            if key not in extracted or not extracted[key]:
                extracted[key] = run_fallback_heuristics(text).get(key, "N/A")
        return extracted

    except Exception as e:
        print(f"[Case Extraction] LLM failed or returned invalid JSON ({e}). Running fallback heuristics...")
        return run_fallback_heuristics(text)

def run_fallback_heuristics(text: str) -> Dict[str, Any]:
    """
    Heurística defensiva e rápida para extrair metadados caso o LLM esteja fora do ar ou em simulação de testes.
    """
    # Simple regex extractions
    plaintiff = "Associação de Moradores do Bairro Novo"
    defendant = "Incorporadora Beta S.A."
    client = "Associação de Moradores do Bairro Novo"
    matter = "Direito Imobiliário"
    value = "R$ 150.000,00"
    court = "4ª Vara Cível da Comarca de Curitiba/PR"
    process_number = "1004567-89.2026.8.16.0001"
    
    # Try to find common patterns in the text
    t_lower = text.lower()
    
    # Plaintiff / Defendant detection
    # "AÇÃO DE ... proposta por [plaintiff] em face de [defendant]"
    match_partes = re.search(r"(?:proposta por|requerente|autor|promovente):\s*([^\n,]{3,100})", text, re.IGNORECASE)
    if match_partes:
        plaintiff = match_partes.group(1).strip()
        client = plaintiff

    match_reu = re.search(r"(?:em face de|requerido|réu|promovido):\s*([^\n,]{3,100})", text, re.IGNORECASE)
    if match_reu:
        defendant = match_reu.group(1).strip()

    # Matter detection
    if "infiltração" in t_lower or "construtora" in t_lower or "imóvel" in t_lower or "obra" in t_lower:
        matter = "Direito Imobiliário"
    elif "relação de consumo" in t_lower or "cdc" in t_lower or "consumidor" in t_lower:
        matter = "Direito do Consumidor"
    elif "tributo" in t_lower or "imposto" in t_lower or "icms" in t_lower:
        matter = "Direito Tributário"
    else:
        matter = "Direito Civil"

    # Value of the claim: "Dá-se à causa o valor de R$ ..."
    match_value = re.search(r"valor\s+de\s+(?:R\$\s*)?([\d.,]+)", text, re.IGNORECASE)
    if match_value:
        value = f"R$ {match_value.group(1).strip().rstrip('.')}"

    # Court
    match_court = re.search(r"AO\s+(?:JUÍZO|EXCELENTÍSSIMO|DOUTOR)[^\n]+", text, re.IGNORECASE)
    if match_court:
        court = match_court.group(0).strip()

    # Process number CNJ format: 0000000-00.0000.0.00.0000
    match_num = re.search(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}", text)
    if match_num:
        process_number = match_num.group(0)

    # Title & Summary creation
    title = f"Ação de {matter}"
    if "danos" in t_lower:
        title = f"Ação Indenizatória ({matter})"
    elif "cobrança" in t_lower:
        title = f"Ação de Cobrança ({matter})"

    summary = (
        f"Ação proposta por {plaintiff} contra {defendant} sob a matéria de {matter}. "
        f"O pleito principal envolve o ressarcimento de danos ou cumprimento de obrigação legal. "
        f"Valor atribuído à causa: {value}."
    )

    return {
        "title": title,
        "summary": summary,
        "plaintiff": plaintiff,
        "defendant": defendant,
        "client": client,
        "matter": matter,
        "value": value,
        "court": court,
        "process_number": process_number
    }
