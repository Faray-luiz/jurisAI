import time
import random
from typing import Dict, Any, Tuple
from backend.app.core.config import settings

# Helper to read configurations from database
def get_agent_config(task_type: str) -> dict:
    from backend.app.db.session import SessionLocal
    from backend.app.db.models import DBAgentConfig
    db = SessionLocal()
    try:
        cfg = db.query(DBAgentConfig).filter(DBAgentConfig.task_type == task_type).first()
        if not cfg:
            cfg = db.query(DBAgentConfig).filter(DBAgentConfig.task_type == "default").first()
        if cfg:
            return {
                "provider": cfg.provider,
                "model": cfg.model,
                "temperature": cfg.temperature,
                "system_prompt": cfg.system_prompt
            }
        return {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.0,
            "system_prompt": "Você é um assistente jurídico de alta precisão."
        }
    finally:
        db.close()

# Pre-defined responses for simulations to guarantee deterministic grounding test cases
MOCK_RESPONSES = {
    "analise_peticao": (
        "Após análise da petição inicial apresentada, constatou-se que o autor fundamenta o pleito indenizatório alegando que a ré descumpriu dever legal. \n\n"
        "Com base nos fatos, a conduta imputada à ré enquadra-se no [Art. 186 do Código Civil], que define o ato ilícito civil pela violação de direito alheio por negligência. "
        "Ademais, a obrigação de indenizar decorre expressamente do [Art. 927 do Código Civil], exigindo a comprovação do nexo causal.\n\n"
        "Contudo, a petição inicial falhou em instruir de forma clara as provas constitutivas de seu direito, em desconformidade com o ônus estabelecido no [Art. 373 do CPC/2015], devendo a parte ré pleitear a improcedência.\n\n"
        "Por fim, ressalta-se a menção a uma norma inválida ou não verificada no rascunho: [Art. 999 do Código de Processo Civil] para fins de tutela de urgência."
    ),
    "rascunho_recurso": (
        "Excelentíssimo Senhor Doutor Juiz de Direito...\n\n"
        "Com amparo no direito à ampla defesa e ao contraditório estabelecido no [Art. 5º da CF/88], a recorrente vem tempestivamente apresentar Recurso.\n\n"
        "O fundamento jurídico baseia-se na violação das formalidades essenciais da petição inicial previstas no [Art. 319 do CPC/2015]. "
        "Ao contrário do sustentado na r sentença, o ônus probatório cabia ao autor de provar o fato alegado, segundo os preceitos do [Art. 373 do CPC/2015].\n\n"
        "Caso esta câmara julgue necessário, pleiteia-se a aplicação analógica do [Art. 1234 da CF/88], que dispõe sobre a revisão imediata de atos processuais."
    ),
    "default": (
        "Com base em suas instruções, elaborei o rascunho de resposta jurídica. \n\n"
        "Conforme previsto no [Art. 5º da CF/88], todos são iguais perante a lei. "
        "Qualquer dano material decorrente de ato ilícito deve observar as regras do [Art. 186 do Código Civil] combinadas com a responsabilidade civil do [Art. 927 do Código Civil].\n\n"
        "Se houver necessidade de revisão técnica, verifique também as regras do [Art. 777 do Código Civil] para contratos de transporte."
    )
}

def route_task(prompt: str, task_type: str = "default") -> Tuple[str, str]:
    """
    Routes the task to the appropriate model and returns (model_name, provider)
    """
    cfg = get_agent_config(task_type)
    return cfg["model"], cfg["provider"]

def generate_response(prompt: str, task_type: str = "default", model_override: str = None) -> Tuple[str, str, int, int]:
    """
    Generates response from selected model or falls back to simulation.
    Returns (response_text, model_used, input_tokens, output_tokens)
    """
    cfg = get_agent_config(task_type)
    model = model_override or cfg["model"]
    provider = cfg["provider"]
    temperature = cfg["temperature"]
    system_prompt = cfg["system_prompt"]
    
    # Calculate mock tokens
    input_tokens = len(prompt.split()) * 2
    
    # Check if API keys are default mock values to run in simulation mode
    is_openai_mock = settings.OPENAI_API_KEY == "mock-openai-key"
    is_anthropic_mock = settings.ANTHROPIC_API_KEY == "mock-anthropic-key"
    is_gemini_mock = settings.GEMINI_API_KEY == "mock-gemini-key"
    
    if (provider == "openai" and is_openai_mock) or \
       (provider == "anthropic" and is_anthropic_mock) or \
       (provider == "google" and is_gemini_mock):
        # Simulation Mode
        time.sleep(1.5)  # Simulate API latency
        response_text = MOCK_RESPONSES.get(task_type, MOCK_RESPONSES["default"])
        output_tokens = len(response_text.split()) * 2
        return response_text, model, input_tokens, output_tokens
        
    # Real integrations
    try:
        if provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            message = client.messages.create(
                model=model,
                max_tokens=2048,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )
            response_text = message.content[0].text
            input_toks = message.usage.input_tokens
            output_toks = message.usage.output_tokens
            return response_text, model, input_toks, output_toks
            
        elif provider == "google" or "gemini" in model.lower():
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model_instance = genai.GenerativeModel(
                model_name=model,
                system_instruction=system_prompt
            )
            response = model_instance.generate_content(
                prompt,
                generation_config={"temperature": temperature}
            )
            response_text = response.text
            # Calculate tokens
            input_toks = len(prompt.split()) * 2
            output_toks = len(response_text.split()) * 2
            return response_text, model, input_toks, output_toks
            
        else: # provider == "openai"
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model=model,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
            )
            response_text = response.choices[0].message.content
            input_toks = response.usage.prompt_tokens
            output_toks = response.usage.completion_tokens
            return response_text, model, input_toks, output_toks
            
    except Exception as e:
        # Fallback to GPT-4o simulation or call
        fallback_model = "gpt-4o"
        if is_openai_mock:
            response_text = f"Fallback ativado devido a erro no provedor original ({e}). " + MOCK_RESPONSES.get(task_type, MOCK_RESPONSES["default"])
            return response_text, fallback_model, input_tokens, len(response_text.split()) * 2
        else:
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model=fallback_model,
                temperature=0.0,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content, fallback_model, response.usage.prompt_tokens, response.usage.completion_tokens
