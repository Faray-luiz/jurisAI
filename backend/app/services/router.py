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

def summarize_history_context(old_messages: list, provider: str) -> str:
    """
    Summarizes older messages using a cheap fast model to preserve context and save tokens.
    """
    summary_prompt = (
        "Você é um copiloto de IA jurídico. Resuma de forma extremamente concisa a conversa jurídica anterior "
        "em um único parágrafo focado nos pontos de direito debatidos, teses levantadas e fatos estabelecidos. "
        "Não adicione introduções ou conclusões, retorne apenas o resumo em português.\n\n"
        "Conversa a ser resumida:\n"
    )
    for msg in old_messages:
        role_label = "Advogado" if msg.get("role") == "user" else "Assistente"
        summary_prompt += f"{role_label}: {msg.get('content')}\n"
    
    try:
        # Check if API keys are default mock values to run in simulation mode
        is_openai_mock = settings.OPENAI_API_KEY == "mock-openai-key" or not settings.OPENAI_API_KEY
        is_anthropic_mock = settings.ANTHROPIC_API_KEY == "mock-anthropic-key" or not settings.ANTHROPIC_API_KEY
        is_gemini_mock = settings.GEMINI_API_KEY == "mock-gemini-key" or not settings.GEMINI_API_KEY
        
        if (provider == "openai" and is_openai_mock) or \
           (provider == "anthropic" and is_anthropic_mock) or \
           (provider == "google" and is_gemini_mock):
            return "Resumo anterior: O advogado consultou sobre conformidade do peticionamento recursal e regras de responsabilidade civil."
        
        if provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            message = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=300,
                temperature=0.0,
                system="Você é um assistente conciso de resumo jurídico.",
                messages=[{"role": "user", "content": summary_prompt}]
            )
            return message.content[0].text
            
        elif provider == "google":
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model_instance = genai.GenerativeModel(
                model_name="gemini-3.5-flash",
                system_instruction="Você é um assistente conciso de resumo jurídico."
            )
            response = model_instance.generate_content(
                summary_prompt,
                generation_config={"temperature": 0.0}
            )
            return response.text
            
        else: # openai
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.0,
                messages=[
                    {"role": "system", "content": "Você é um assistente conciso de resumo jurídico."},
                    {"role": "user", "content": summary_prompt}
                ]
            )
            return response.choices[0].message.content
    except Exception as e:
        return f"Resumo automático (Erro na chamada do LLM de resumo: {e}): Histórico de interações e teses jurídicas analisadas previamente."

from backend.app.services.resilience import execute_with_retry_and_breaker, get_breaker

@execute_with_retry_and_breaker(provider_name="anthropic")
def _call_anthropic(client, model_id, temperature, system_blocks, messages_payload):
    return client.messages.create(
        model=model_id,
        max_tokens=8192,
        temperature=temperature,
        system=system_blocks,
        messages=messages_payload
    )

@execute_with_retry_and_breaker(provider_name="google")
def _call_google(model_instance, contents, temperature):
    return model_instance.generate_content(
        contents,
        generation_config={"temperature": temperature}
    )

@execute_with_retry_and_breaker(provider_name="openai")
def _call_openai(client, model, temperature, messages_payload):
    return client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=messages_payload
    )

def _log_to_langsmith(provider: str, model: str, prompt: str, system_prompt: str, response: str, tokens_in: int, tokens_out: int):
    if not settings.LANGSMITH_API_KEY:
        return
    try:
        import requests
        try:
            from langsmith import Client
            client = Client(api_url="https://api.smith.langchain.com", api_key=settings.LANGSMITH_API_KEY)
            client.create_run(
                name=f"JurisAI - {provider} - {model}",
                run_type="llm",
                inputs={"prompt": prompt, "system_prompt": system_prompt},
                outputs={"response": response},
                project_name=settings.LANGSMITH_PROJECT,
                extra={
                    "metadata": {
                        "provider": provider,
                        "model": model,
                        "tokens_in": tokens_in,
                        "tokens_out": tokens_out
                    }
                }
            )
            print("[LangSmith] Run successfully logged via SDK.")
        except ImportError:
            import uuid
            run_id = str(uuid.uuid4())
            payload = {
                "id": run_id,
                "name": f"JurisAI - {provider} - {model}",
                "run_type": "llm",
                "inputs": {"prompt": prompt, "system_prompt": system_prompt},
                "outputs": {"response": response},
                "session_name": settings.LANGSMITH_PROJECT,
                "extra": {
                    "metadata": {
                        "provider": provider,
                        "model": model,
                        "tokens_in": tokens_in,
                        "tokens_out": tokens_out
                    }
                }
            }
            headers = {
                "x-api-key": settings.LANGSMITH_API_KEY,
                "Content-Type": "application/json"
            }
            res = requests.post("https://api.smith.langchain.com/runs", json=payload, headers=headers, timeout=2.0)
            if res.status_code in [200, 201]:
                print("[LangSmith] Run successfully logged via REST API.")
            else:
                print(f"[LangSmith] API post returned status {res.status_code}: {res.text}")
    except Exception as e:
        print(f"[LangSmith Logging Error] Graceful fallback active: {e}")

def generate_response(prompt: str, task_type: str = "default", model_override: str = None, history: list = None) -> Tuple[str, str, int, int]:
    """
    Generates response from selected model or falls back to simulation.
    Supports dynamic RAG context injection, prompt caching, and rolling window history summarization.
    Returns (response_text, model_used, input_tokens, output_tokens)
    """
    cfg = get_agent_config(task_type)
    model = model_override or cfg["model"]
    provider = cfg["provider"]
    temperature = cfg["temperature"]
    system_prompt = cfg["system_prompt"]
    
    # 1. Retrieve RAG Context dynamically — Mission-Aware Top-K Semantic Search
    from backend.app.services.vector_store import query_vector_store
    rag_context = ""
    try:
        rag_results = query_vector_store(query=prompt, task_type=task_type, top_k=3)
        if rag_results:
            rag_context = (
                "Use os seguintes dispositivos legais, selecionados por relavância para esta consulta, "
                "para fundamentar sua resposta com precisão jurídica:\n\n"
            )
            rag_context += "\n\n".join(
                [f"### {r['citation']} ({r['source']})\n{r['text']}" for r in rag_results]
            )
            print(f"[RAG] task_type='{task_type}' → {len(rag_results)} doc(s) retrieved: "
                  f"{[r['citation'] for r in rag_results]}")
    except Exception as e:
        print(f"[RAG] Error retrieving mission-aware context: {e}")

    # 2. Process History with Rolling Window Summarization (Compress if > 6 messages)
    processed_history = []
    if history and len(history) > 0:
        if len(history) > 6:
            compress_slice = history[:-4]
            preserve_slice = history[-4:]
            
            summary = summarize_history_context(compress_slice, provider)
            
            processed_history.append({
                "role": "user",
                "content": f"[Histórico anterior resumido para economia de tokens: {summary}]"
            })
            processed_history.append({
                "role": "assistant",
                "content": "Entendido perfeitamente. Como posso ajudar com as próximas etapas com base nesse histórico?"
            })
            
            for msg in preserve_slice:
                processed_history.append({
                    "role": "user" if msg.get("role") == "user" else "assistant",
                    "content": msg.get("content")
                })
        else:
            for msg in history:
                processed_history.append({
                    "role": "user" if msg.get("role") == "user" else "assistant",
                    "content": msg.get("content")
                })

    input_tokens = len(prompt.split()) * 2
    if history:
        input_tokens += sum(len(m.get("content", "").split()) for m in history) * 2
    
    is_openai_mock = settings.OPENAI_API_KEY == "mock-openai-key" or not settings.OPENAI_API_KEY
    is_anthropic_mock = settings.ANTHROPIC_API_KEY == "mock-anthropic-key" or not settings.ANTHROPIC_API_KEY
    is_gemini_mock = settings.GEMINI_API_KEY == "mock-gemini-key" or not settings.GEMINI_API_KEY
    
    if (provider == "openai" and is_openai_mock) or \
       (provider == "anthropic" and is_anthropic_mock) or \
       (provider == "google" and is_gemini_mock):
        time.sleep(1.5)
        response_text = MOCK_RESPONSES.get(task_type, MOCK_RESPONSES["default"])
        output_tokens = len(response_text.split()) * 2
        _log_to_langsmith(provider, model, prompt, system_prompt, response_text, input_tokens, output_tokens)
        return response_text, model, input_tokens, output_tokens
        
    try:
        # Check circuit breaker before proceeding with real integration
        breaker = get_breaker(provider)
        if not breaker.allow_request():
            print(f"[Resilience Warning] Circuit breaker for provider '{provider}' is OPEN. Immediate fallback triggered.")
            raise RuntimeError(f"Circuit breaker for provider '{provider}' is OPEN.")

        if provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            model_id = "claude-sonnet-4-6" if model in ["claude-3-5-sonnet", "claude-3-5-sonnet-latest", "claude-3-5-sonnet-20241022", "claude-3-5-sonnet-20240620"] else model
            
            system_blocks = [
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"}
                }
            ]
            if rag_context:
                system_blocks.append({
                    "type": "text",
                    "text": rag_context,
                    "cache_control": {"type": "ephemeral"}
                })
            
            messages_payload = []
            for msg in processed_history:
                messages_payload.append({
                    "role": "user" if msg["role"] == "user" else "assistant",
                    "content": msg["content"]
                })
            messages_payload.append({"role": "user", "content": prompt})
            
            message = _call_anthropic(client, model_id, temperature, system_blocks, messages_payload)
            response_text = message.content[0].text
            input_toks = message.usage.input_tokens
            output_toks = message.usage.output_tokens
            _log_to_langsmith(provider, model, prompt, system_prompt, response_text, input_toks, output_toks)
            return response_text, model, input_toks, output_toks
            
        elif provider == "google" or "gemini" in model.lower():
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            full_system = system_prompt
            if rag_context:
                full_system += f"\n\n{rag_context}"
                
            model_instance = genai.GenerativeModel(
                model_name=model,
                system_instruction=full_system
            )
            
            contents = []
            for msg in processed_history:
                role = "user" if msg["role"] == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [msg["content"]]
                })
            contents.append({
                "role": "user",
                "parts": [prompt]
            })
            
            response = _call_google(model_instance, contents, temperature)
            response_text = response.text
            input_toks = len(prompt.split()) * 2
            output_toks = len(response_text.split()) * 2
            _log_to_langsmith(provider, model, prompt, system_prompt, response_text, input_toks, output_toks)
            return response_text, model, input_toks, output_toks
            
        else: # provider == "openai"
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            
            messages_payload = []
            full_system = system_prompt
            if rag_context:
                full_system += f"\n\n{rag_context}"
                
            messages_payload.append({"role": "system", "content": full_system})
            
            for msg in processed_history:
                messages_payload.append({
                    "role": "user" if msg["role"] == "user" else "assistant",
                    "content": msg["content"]
                })
            messages_payload.append({"role": "user", "content": prompt})
            
            response = _call_openai(client, model, temperature, messages_payload)
            response_text = response.choices[0].message.content
            input_toks = response.usage.prompt_tokens
            output_toks = response.usage.completion_tokens
            _log_to_langsmith(provider, model, prompt, system_prompt, response_text, input_toks, output_toks)
            return response_text, model, input_toks, output_toks
            
    except Exception as e:
        # Fallback to GPT-4o
        fallback_model = "gpt-4o"
        print(f"[Resilience] Exception occurred during call: {e}. Executing fallback to {fallback_model}.")
        if is_openai_mock:
            response_text = f"Fallback ativado devido a erro no provedor original ({e}). " + MOCK_RESPONSES.get(task_type, MOCK_RESPONSES["default"])
            _log_to_langsmith("openai", fallback_model, prompt, system_prompt, response_text, input_tokens, len(response_text.split()) * 2)
            return response_text, fallback_model, input_tokens, len(response_text.split()) * 2
        else:
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            
            full_system = system_prompt
            if rag_context:
                full_system += f"\n\n{rag_context}"
                
            messages_payload = [
                {"role": "system", "content": full_system}
            ]
            for msg in processed_history:
                messages_payload.append({
                    "role": "user" if msg["role"] == "user" else "assistant",
                    "content": msg["content"]
                })
            messages_payload.append({"role": "user", "content": prompt})
            
            # Execute fallback with OpenAI resilience/circuit breaker
            try:
                response = _call_openai(client, fallback_model, 0.0, messages_payload)
                response_text = response.choices[0].message.content
                input_toks = response.usage.prompt_tokens
                output_toks = response.usage.completion_tokens
                _log_to_langsmith("openai", fallback_model, prompt, system_prompt, response_text, input_toks, output_toks)
                return response_text, fallback_model, input_toks, output_toks
            except Exception as fb_err:
                print(f"[Resilience] Fallback failed: {fb_err}. Returning simulation fallback.")
                response_text = f"Fallback emergencial ativado devido a erro duplo ({e} / {fb_err}). " + MOCK_RESPONSES.get(task_type, MOCK_RESPONSES["default"])
                _log_to_langsmith("openai", fallback_model, prompt, system_prompt, response_text, input_tokens, len(response_text.split()) * 2)
                return response_text, fallback_model, input_tokens, len(response_text.split()) * 2

