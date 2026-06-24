from fastapi import FastAPI, HTTPException, Depends, Security, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import time

from backend.app.core.config import settings
from backend.app.core.security import get_current_user, verify_process_access
from backend.app.db.session import (
    get_db_user, get_all_db_users, get_all_db_processes, 
    get_all_db_audits, update_db_user_quota_limit, add_audit_log
)
from backend.app.services.router import route_task, generate_response
from backend.app.services.grounding import verify_citations
from backend.app.services.guardrails import validate_input_prompt, redact_pii, sanitize_document_content
from backend.app.services.quota import estimate_request_cost, verify_and_update_quota, commit_quota_usage

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

# Enable CORS for Next.js frontend
origins = [org.strip() for org in settings.ALLOWED_ORIGINS.split(",") if org.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Payloads
class MessagePayload(BaseModel):
    role: str
    content: str

class ChatPayload(BaseModel):
    prompt: str
    process_id: Optional[str] = None
    task_type: str = "default"  # analise_peticao, rascunho_recurso, default
    model_override: Optional[str] = None
    history: Optional[List[MessagePayload]] = None

class QuotaUpdatePayload(BaseModel):
    email: str
    limit: float

# Routes
@app.get("/")
def read_root():
    return {"status": "ok", "app": settings.PROJECT_NAME, "version": settings.VERSION}

@app.get("/api/v1/users/me")
def get_me(user: dict = Depends(get_current_user)):
    return {
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "quota_limit": user["quota_limit"],
        "quota_spent": user["quota_spent"],
        "assigned_clients": user["assigned_clients"]
    }

@app.get("/api/v1/processes")
def get_processes(user: dict = Depends(get_current_user)):
    # Filter processes based on Ethical Wall
    accessible_processes = []
    processes = get_all_db_processes()
    for proc in processes:
        if proc["client"] not in user.get("conflicted_clients", []):
            # Only Advogado/Sócio can see details
            if user["role"] not in ["Compliance", "TI"]:
                accessible_processes.append(proc)
    return accessible_processes

@app.post("/api/v1/chat")
def chat_interaction(payload: ChatPayload, user: dict = Depends(get_current_user)):
    # 1. Guardrail: Anti Prompt Injection
    validate_input_prompt(payload.prompt)
    
    # 2. Ethical Wall checking
    if payload.process_id and payload.process_id != "N/A":
        verify_process_access(payload.process_id, user)
        
    # 3. Model routing logic
    model, provider = route_task(payload.prompt, payload.task_type)
    if payload.model_override:
        model = payload.model_override
        
    # Check for economic routing fallback if enabled and user has spent >= 80% cota
    from backend.app.db.session import get_db_system_settings
    sys_settings = get_db_system_settings()
    enable_economic_routing = sys_settings.get("enable_economic_routing", "false").lower() == "true"
    
    if enable_economic_routing and user["quota_limit"] > 0:
        if user["quota_spent"] / user["quota_limit"] >= 0.8:
            # Downgrade to cheaper model
            if provider == "openai" and model != "gpt-4o-mini":
                model = "gpt-4o-mini"
            elif provider == "anthropic" and model != "claude-haiku-4-5":
                model = "claude-haiku-4-5"
            elif provider == "google" and model != "gemini-3.5-flash":
                model = "gemini-3.5-flash"
        
    # 4. Quota check: pre-flight estimation
    estimated_cost = estimate_request_cost(payload.prompt, model)
    quota_status = verify_and_update_quota(user["email"], estimated_cost)
    
    if not quota_status["allowed"]:
        add_audit_log(
            user["email"],
            payload.task_type,
            payload.process_id or "N/A",
            model,
            0.0,
            "Rejeitado (Cota Insuficiente)",
            payload.prompt,
            quota_status["message"],
            "Bloqueado"
        )
        raise HTTPException(status_code=402, detail=quota_status["message"])
        
    # 5. Generate LLM response (or simulation)
    history_list = [{"role": h.role, "content": h.content} for h in payload.history] if payload.history else None
    raw_response, model_used, input_tokens, output_tokens = generate_response(
        payload.prompt, payload.task_type, payload.model_override, history=history_list
    )
    
    # 6. Sychronous Grounding check
    citations = verify_citations(raw_response)
    
    grounding_status = "Verificado"
    if any(c["status"] == "warn" for c in citations):
        grounding_status = "Não Verificado"
    elif any(c["status"] == "review" for c in citations):
        grounding_status = "Em Revisão"
        
    # 7. Output sanitization: PII redaction
    sanitized_response = redact_pii(raw_response)
    
    # Calculate final cost
    price_info = settings.MODEL_PRICING.get(model_used, {"input": 0.00015, "output": 0.0006})
    actual_cost = ((input_tokens / 1000.0) * price_info["input"]) + ((output_tokens / 1000.0) * price_info["output"])
    
    # Update quota in database
    commit_quota_usage(user["email"], actual_cost)
    
    # 8. Record audit log
    add_audit_log(
        user["email"],
        payload.task_type,
        payload.process_id or "N/A",
        model_used,
        actual_cost,
        "Sucesso",
        payload.prompt,
        sanitized_response,
        grounding_status
    )
    
    return {
        "response": sanitized_response,
        "citations": citations,
        "model_used": model_used,
        "cost_usd": actual_cost,
        "quota_status": quota_status["status"],
        "quota_warning": quota_status.get("warning", False)
    }

@app.post("/api/v1/chat/sanitize-doc")
def sanitize_doc(payload: Dict[str, str], user: dict = Depends(get_current_user)):
    content = payload.get("content", "")
    if not content:
        raise HTTPException(status_code=400, detail="Conteúdo do documento não fornecido.")
    
    sanitized = sanitize_document_content(content)
    return {"sanitized_content": sanitized}

@app.get("/api/v1/admin/audits")
def get_audits(user: dict = Depends(get_current_user)):
    # Segregation of duties: only Compliance and Sócio can see audits
    if user["role"] not in ["Compliance", "Sócio"]:
        raise HTTPException(
            status_code=403,
            detail="Apenas membros de Compliance ou Sócios possuem permissão para auditar logs."
        )
    return get_all_db_audits()

@app.post("/api/v1/admin/quotas")
def update_quota(payload: QuotaUpdatePayload, user: dict = Depends(get_current_user)):
    # Only Sócio can change quotas
    if user["role"] not in ["Sócio"]:
        raise HTTPException(
            status_code=403,
            detail="Acesso negado: apenas Sócios podem alterar limites orçamentários."
        )
    
    db_user = get_db_user(payload.email)
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
        
    update_db_user_quota_limit(payload.email, payload.limit)
    return {"message": f"Limite de cota de {payload.email} atualizado para ${payload.limit:.2f}"}

@app.get("/api/v1/admin/users")
def get_users_list(user: dict = Depends(get_current_user)):
    if user["role"] not in ["Sócio", "Compliance"]:
         raise HTTPException(status_code=403, detail="Acesso não autorizado.")
    return get_all_db_users()


# Models for Admin Endpoints
class AgentConfigPayload(BaseModel):
    task_type: str
    provider: str
    model: str
    temperature: float
    system_prompt: str

class GroundingDocPayload(BaseModel):
    key: str
    citation: str
    text: str
    source: str
    agent_task_type: str = "global"

class UserCreatePayload(BaseModel):
    email: str
    name: str
    role: str
    quota_limit: float

# Admin endpoints

@app.get("/api/v1/admin/agent-configs")
def get_agent_configs(user: dict = Depends(get_current_user)):
    if user["role"] not in ["Sócio", "Compliance"]:
        raise HTTPException(status_code=403, detail="Acesso restrito.")
    from backend.app.db.session import SessionLocal
    from backend.app.db.models import DBAgentConfig
    db = SessionLocal()
    try:
        cfgs = db.query(DBAgentConfig).all()
        return [{
            "id": c.id,
            "task_type": c.task_type,
            "provider": c.provider,
            "model": c.model,
            "temperature": c.temperature,
            "system_prompt": c.system_prompt
        } for c in cfgs]
    finally:
        db.close()

@app.post("/api/v1/admin/agent-configs")
def update_agent_config(payload: AgentConfigPayload, user: dict = Depends(get_current_user)):
    if user["role"] not in ["Sócio", "Compliance"]:
        raise HTTPException(status_code=403, detail="Acesso restrito.")
    from backend.app.db.session import SessionLocal
    from backend.app.db.models import DBAgentConfig
    db = SessionLocal()
    try:
        cfg = db.query(DBAgentConfig).filter(DBAgentConfig.task_type == payload.task_type).first()
        if not cfg:
            cfg = DBAgentConfig(task_type=payload.task_type)
            db.add(cfg)
        cfg.provider = payload.provider
        cfg.model = payload.model
        cfg.temperature = payload.temperature
        cfg.system_prompt = payload.system_prompt
        db.commit()
        return {"status": "ok", "message": f"Configuração de '{payload.task_type}' salva com sucesso."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()

@app.get("/api/v1/admin/grounding-docs")
def get_grounding_docs(user: dict = Depends(get_current_user)):
    if user["role"] not in ["Sócio", "Compliance"]:
        raise HTTPException(status_code=403, detail="Acesso restrito.")
    from backend.app.db.session import SessionLocal
    from backend.app.db.models import DBGroundingDoc
    db = SessionLocal()
    try:
        docs = db.query(DBGroundingDoc).all()
        return [{
            "id": d.id,
            "key": d.key,
            "citation": d.citation,
            "text": d.text,
            "source": d.source,
            "is_active": d.is_active,
            "agent_task_type": d.agent_task_type or "global"
        } for d in docs]
    finally:
        db.close()

@app.post("/api/v1/admin/grounding-docs")
def update_grounding_doc(payload: GroundingDocPayload, user: dict = Depends(get_current_user)):
    if user["role"] not in ["Sócio", "Compliance"]:
        raise HTTPException(status_code=403, detail="Acesso restrito.")
    from backend.app.db.session import SessionLocal
    from backend.app.db.models import DBGroundingDoc
    db = SessionLocal()
    try:
        doc = db.query(DBGroundingDoc).filter(DBGroundingDoc.key == payload.key).first()
        if not doc:
            doc = DBGroundingDoc(key=payload.key)
            db.add(doc)
        doc.citation = payload.citation
        doc.text = payload.text
        doc.source = payload.source
        doc.is_active = True
        doc.agent_task_type = payload.agent_task_type or "global"
        db.commit()
        return {"status": "ok", "message": f"Documento '{payload.citation}' salvo com sucesso."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()

@app.post("/api/v1/admin/grounding-docs/upload-pdf")
def upload_grounding_pdf(
    citation: str = Form(...),
    source: str = Form(...),
    agent_task_type: str = Form("global"),
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    if user["role"] not in ["Sócio", "Compliance"]:
        raise HTTPException(status_code=403, detail="Acesso restrito.")
    from backend.app.db.session import SessionLocal
    from backend.app.db.models import DBGroundingDoc
    from backend.app.services.pdf_extractor import extract_text_from_pdf
    
    try:
        pdf_bytes = file.file.read()
        extracted_text = extract_text_from_pdf(pdf_bytes)
        if not extracted_text:
            raise HTTPException(status_code=400, detail="Não foi possível extrair nenhum texto legível do PDF.")
            
        # Generate simple key
        import re
        key = re.sub(r"[^\w]", "", citation.lower()).strip()
        if not key:
            key = f"doc_{int(time.time())}"
            
        db = SessionLocal()
        try:
            doc = db.query(DBGroundingDoc).filter(DBGroundingDoc.key == key).first()
            if not doc:
                doc = DBGroundingDoc(key=key)
                db.add(doc)
            doc.citation = citation
            doc.text = extracted_text
            doc.source = source
            doc.is_active = True
            doc.agent_task_type = agent_task_type or "global"
            db.commit()
            return {"status": "ok", "message": f"PDF carregado e salvo como citação '{citation}' para missão '{agent_task_type}'."}
        finally:
            db.close()
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/v1/admin/grounding-docs/{doc_id}")
def delete_grounding_doc(doc_id: int, user: dict = Depends(get_current_user)):
    if user["role"] not in ["Sócio", "Compliance"]:
        raise HTTPException(status_code=403, detail="Acesso restrito.")
    from backend.app.db.session import SessionLocal
    from backend.app.db.models import DBGroundingDoc
    db = SessionLocal()
    try:
        doc = db.query(DBGroundingDoc).filter(DBGroundingDoc.id == doc_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Documento não encontrado.")
        db.delete(doc)
        db.commit()
        return {"status": "ok", "message": "Documento excluído com sucesso."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()

@app.post("/api/v1/admin/users")
def admin_create_user(payload: UserCreatePayload, user: dict = Depends(get_current_user)):
    if user["role"] not in ["Sócio"]:
        raise HTTPException(status_code=403, detail="Apenas Sócios podem criar usuários manualmente.")
    from backend.app.db.session import SessionLocal
    from backend.app.db.models import DBUser
    db = SessionLocal()
    try:
        existing = db.query(DBUser).filter(DBUser.email == payload.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Usuário já cadastrado.")
            
        new_u = DBUser(
            email=payload.email,
            name=payload.name,
            role=payload.role,
            quota_limit=payload.quota_limit,
            quota_spent=0.0,
            assigned_clients=["Companhia Gama"] if payload.role == "Advogado" else [],
            conflicted_clients=[]
        )
        db.add(new_u)
        db.commit()
        return {"status": "ok", "message": f"Usuário {payload.name} criado com sucesso."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()

class SystemSettingsUpdatePayload(BaseModel):
    enable_economic_routing: bool
    enable_global_budget: bool
    enable_client_billing: bool

class RefillPayload(BaseModel):
    provider: str
    amount: float

@app.get("/api/v1/admin/system-settings")
def get_system_settings(user: dict = Depends(get_current_user)):
    if user["role"] not in ["Sócio"]:
        raise HTTPException(status_code=403, detail="Acesso restrito.")
    from backend.app.db.session import get_db_system_settings, SessionLocal, update_db_system_setting
    from backend.app.db.models import DBAuditLog
    
    settings_dict = get_db_system_settings()
    
    # Calculate spent by provider from audit logs
    db = SessionLocal()
    try:
        logs = db.query(DBAuditLog).all()
        openai_spent = sum(l.cost_usd for l in logs if "gpt" in l.model.lower())
        anthropic_spent = sum(l.cost_usd for l in logs if "claude" in l.model.lower())
        google_spent = sum(l.cost_usd for l in logs if "gemini" in l.model.lower())
    except Exception:
        openai_spent = 0.0
        anthropic_spent = 0.0
        google_spent = 0.0
    finally:
        db.close()
        
    openai_added = float(settings_dict.get("openai_credits_added", "5.0"))
    anthropic_added = float(settings_dict.get("anthropic_credits_added", "5.0"))
    google_added = float(settings_dict.get("google_credits_added", "5.0"))
    
    openai_remaining = max(openai_added - openai_spent, 0.0)
    anthropic_remaining = max(anthropic_added - anthropic_spent, 0.0)
    google_remaining = max(google_added - google_spent, 0.0)
    
    consolidated_balance = openai_remaining + anthropic_remaining + google_remaining
    
    # Update global_budget setting dynamically in the DB to enforce it
    update_db_system_setting("global_budget", f"{consolidated_balance:.6f}")
    
    return {
        "global_budget": consolidated_balance,
        "enable_economic_routing": settings_dict.get("enable_economic_routing", "false").lower() == "true",
        "enable_global_budget": settings_dict.get("enable_global_budget", "true").lower() == "true",
        "enable_client_billing": settings_dict.get("enable_client_billing", "true").lower() == "true",
        "openai_credits_added": openai_added,
        "anthropic_credits_added": anthropic_added,
        "google_credits_added": google_added,
        "openai_spent": openai_spent,
        "anthropic_spent": anthropic_spent,
        "google_spent": google_spent,
        "openai_remaining": openai_remaining,
        "anthropic_remaining": anthropic_remaining,
        "google_remaining": google_remaining
    }

@app.post("/api/v1/admin/system-settings")
def update_system_settings(payload: SystemSettingsUpdatePayload, user: dict = Depends(get_current_user)):
    if user["role"] not in ["Sócio"]:
        raise HTTPException(status_code=403, detail="Acesso restrito.")
    from backend.app.db.session import update_db_system_setting
    update_db_system_setting("enable_economic_routing", str(payload.enable_economic_routing).lower())
    update_db_system_setting("enable_global_budget", str(payload.enable_global_budget).lower())
    update_db_system_setting("enable_client_billing", str(payload.enable_client_billing).lower())
    return {"status": "ok", "message": "Configurações do sistema atualizadas com sucesso."}

@app.post("/api/v1/admin/system-settings/refill")
def add_refill(payload: RefillPayload, user: dict = Depends(get_current_user)):
    if user["role"] not in ["Sócio"]:
        raise HTTPException(status_code=403, detail="Acesso restrito.")
    if payload.provider not in ["openai", "anthropic", "google"]:
        raise HTTPException(status_code=400, detail="Provedor inválido.")
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="O valor da recarga deve ser positivo.")
        
    from backend.app.db.session import get_db_system_settings, update_db_system_setting
    settings_dict = get_db_system_settings()
    
    key = f"{payload.provider}_credits_added"
    current_added = float(settings_dict.get(key, "5.0"))
    new_total = current_added + payload.amount
    
    update_db_system_setting(key, f"{new_total:.2f}")
    return {"status": "ok", "message": f"Recarga de ${payload.amount:.2f} registrada com sucesso para {payload.provider.upper()}."}

@app.get("/api/v1/admin/metrics")
def get_admin_metrics(user: dict = Depends(get_current_user)):
    if user["role"] not in ["Sócio", "Compliance"]:
        raise HTTPException(status_code=403, detail="Acesso restrito.")
    from backend.app.db.session import SessionLocal
    from backend.app.db.models import DBAuditLog, DBUser
    db = SessionLocal()
    try:
        logs = db.query(DBAuditLog).all()
        users = db.query(DBUser).all()
        
        total_queries = len(logs)
        total_cost = sum(l.cost_usd for l in logs)
        
        # Cost by user
        cost_by_user = {}
        for l in logs:
            cost_by_user[l.user_email] = cost_by_user.get(l.user_email, 0.0) + l.cost_usd
            
        # Cost by agent
        cost_by_agent = {}
        for l in logs:
            cost_by_agent[l.action] = cost_by_agent.get(l.action, 0.0) + l.cost_usd
            
        # Grounding status distribution
        from backend.app.db.models import DBProcess
        processes = db.query(DBProcess).all()
        process_map = {p.id: {"client": p.client, "title": p.title, "number": p.process_number} for p in processes}
        
        cost_by_client = {}
        for l in logs:
            p_info = process_map.get(l.process_id)
            client_name = p_info["client"] if p_info else "Geral / Sem Processo"
            
            if client_name not in cost_by_client:
                cost_by_client[client_name] = {
                    "total_cost": 0.0,
                    "queries_count": 0,
                    "processes": {}
                }
            
            cost_by_client[client_name]["total_cost"] += l.cost_usd
            cost_by_client[client_name]["queries_count"] += 1
            
            p_id = l.process_id or "N/A"
            p_title = p_info["title"] if p_info else "Interações Gerais"
            p_number = p_info["number"] if p_info else "N/A"
            
            if p_id not in cost_by_client[client_name]["processes"]:
                cost_by_client[client_name]["processes"][p_id] = {
                    "process_id": p_id,
                    "title": p_title,
                    "number": p_number,
                    "cost": 0.0,
                    "queries": 0
                }
            cost_by_client[client_name]["processes"][p_id]["cost"] += l.cost_usd
            cost_by_client[client_name]["processes"][p_id]["queries"] += 1

        # Format processes as a list for cleaner frontend handling
        for client_name, client_data in cost_by_client.items():
            client_data["processes"] = list(client_data["processes"].values())

        grounding_dist = {}
        for l in logs:
            grounding_dist[l.grounding_status] = grounding_dist.get(l.grounding_status, 0) + 1
            
        return {
            "total_queries": total_queries,
            "total_cost": total_cost,
            "cost_by_user": cost_by_user,
            "cost_by_agent": cost_by_agent,
            "cost_by_client": cost_by_client,
            "grounding_dist": grounding_dist,
            "user_count": len(users)
        }
    finally:
        db.close()

@app.get("/api/v1/admin/provider-status")
def get_provider_status(user: dict = Depends(get_current_user)):
    if user["role"] not in ["Sócio"]:
        raise HTTPException(status_code=403, detail="Apenas Sócios podem auditar chaves de API.")
    
    status = {}
    
    # OpenAI
    is_openai_mock = settings.OPENAI_API_KEY == "mock-openai-key" or not settings.OPENAI_API_KEY
    if is_openai_mock:
        status["openai"] = {"status": "simulado", "message": "Usando simulação ('mock-openai-key')"}
    else:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=1,
                messages=[{"role": "user", "content": "ping"}]
            )
            status["openai"] = {"status": "ativo", "message": "Conexão ativa e modelo gpt-4o-mini disponível"}
        except Exception as e:
            status["openai"] = {"status": "erro", "message": f"Falha na API: {str(e)}"}
            
    # Anthropic
    is_anthropic_mock = settings.ANTHROPIC_API_KEY == "mock-anthropic-key" or not settings.ANTHROPIC_API_KEY
    if is_anthropic_mock:
        status["anthropic"] = {"status": "simulado", "message": "Usando simulação ('mock-anthropic-key')"}
    else:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=1,
                messages=[{"role": "user", "content": "ping"}]
            )
            status["anthropic"] = {"status": "ativo", "message": "Conexão ativa e modelo claude-haiku-4-5 disponível"}
        except Exception as e:
            status["anthropic"] = {"status": "erro", "message": f"Falha na API: {str(e)}"}
            
    # Google (Gemini)
    is_gemini_mock = settings.GEMINI_API_KEY == "mock-gemini-key" or not settings.GEMINI_API_KEY
    if is_gemini_mock:
        status["google"] = {"status": "simulado", "message": "Usando simulação ('mock-gemini-key')"}
    else:
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-3.5-flash")
            model.generate_content("ping")
            status["google"] = {"status": "ativo", "message": "Conexão ativa e modelo gemini-3.5-flash disponível"}
        except Exception as e:
            status["google"] = {"status": "erro", "message": f"Falha na API: {str(e)}"}
            
    return status


# ─── Missions ────────────────────────────────────────────────────────────────

class MissionCreatePayload(BaseModel):
    task_type: str
    display_name: str
    icon: str = "⚖️"
    description: str = ""
    default_prompt: str = ""
    system_prompt: str = ""
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    temperature: float = 0.0
    is_active: bool = True


@app.get("/api/v1/missions")
def get_active_missions(user: dict = Depends(get_current_user)):
    """Returns active missions visible to all authenticated users (lawyers)."""
    from backend.app.db.session import SessionLocal
    from backend.app.db.models import DBMission
    db = SessionLocal()
    try:
        missions = db.query(DBMission).filter(DBMission.is_active == True).order_by(DBMission.id).all()
        return [{
            "id": m.id,
            "task_type": m.task_type,
            "display_name": m.display_name,
            "icon": m.icon,
            "description": m.description,
            "default_prompt": m.default_prompt,
        } for m in missions]
    finally:
        db.close()


@app.get("/api/v1/admin/missions")
def get_all_missions(user: dict = Depends(get_current_user)):
    """Returns ALL missions (active and inactive) for admin management."""
    if user["role"] not in ["Sócio"]:
        raise HTTPException(status_code=403, detail="Apenas Sócios podem gerenciar missões.")
    from backend.app.db.session import SessionLocal
    from backend.app.db.models import DBMission
    db = SessionLocal()
    try:
        missions = db.query(DBMission).order_by(DBMission.id).all()
        return [{
            "id": m.id,
            "task_type": m.task_type,
            "display_name": m.display_name,
            "icon": m.icon,
            "description": m.description,
            "default_prompt": m.default_prompt,
            "is_active": m.is_active,
            "created_at": m.created_at,
        } for m in missions]
    finally:
        db.close()


@app.post("/api/v1/admin/missions")
def upsert_mission(payload: MissionCreatePayload, user: dict = Depends(get_current_user)):
    """Creates or updates a mission and its matching AgentConfig."""
    if user["role"] not in ["Sócio"]:
        raise HTTPException(status_code=403, detail="Apenas Sócios podem criar ou editar missões.")
    from backend.app.db.session import SessionLocal
    from backend.app.db.models import DBMission, DBAgentConfig
    db = SessionLocal()
    try:
        # Upsert mission
        mission = db.query(DBMission).filter(DBMission.task_type == payload.task_type).first()
        is_new = mission is None
        if is_new:
            mission = DBMission(task_type=payload.task_type, created_at=time.time())
            db.add(mission)

        mission.display_name = payload.display_name
        mission.icon = payload.icon
        mission.description = payload.description
        mission.default_prompt = payload.default_prompt
        mission.is_active = payload.is_active

        # Upsert matching AgentConfig
        cfg = db.query(DBAgentConfig).filter(DBAgentConfig.task_type == payload.task_type).first()
        if not cfg:
            cfg = DBAgentConfig(task_type=payload.task_type)
            db.add(cfg)
        cfg.provider = payload.provider
        cfg.model = payload.model
        cfg.temperature = payload.temperature
        cfg.system_prompt = payload.system_prompt or f"Você é um assistente jurídico especializado em: {payload.display_name}."

        db.commit()
        action = "criada" if is_new else "atualizada"
        return {"status": "ok", "message": f"Missão '{payload.display_name}' {action} com sucesso."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


@app.delete("/api/v1/admin/missions/{mission_id}")
def delete_mission(mission_id: int, user: dict = Depends(get_current_user)):
    """Deletes a mission by ID."""
    if user["role"] not in ["Sócio"]:
        raise HTTPException(status_code=403, detail="Apenas Sócios podem excluir missões.")
    from backend.app.db.session import SessionLocal
    from backend.app.db.models import DBMission
    db = SessionLocal()
    try:
        mission = db.query(DBMission).filter(DBMission.id == mission_id).first()
        if not mission:
            raise HTTPException(status_code=404, detail="Missão não encontrada.")
        db.delete(mission)
        db.commit()
        return {"status": "ok", "message": f"Missão '{mission.display_name}' excluída com sucesso."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()
