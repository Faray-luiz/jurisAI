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
class ChatPayload(BaseModel):
    prompt: str
    process_id: Optional[str] = None
    task_type: str = "default"  # analise_peticao, rascunho_recurso, default
    model_override: Optional[str] = None

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
    raw_response, model_used, input_tokens, output_tokens = generate_response(
        payload.prompt, payload.task_type, payload.model_override
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
            "is_active": d.is_active
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
            db.commit()
            return {"status": "ok", "message": f"PDF carregado e salvo como citação '{citation}'."}
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
        grounding_dist = {}
        for l in logs:
            grounding_dist[l.grounding_status] = grounding_dist.get(l.grounding_status, 0) + 1
            
        return {
            "total_queries": total_queries,
            "total_cost": total_cost,
            "cost_by_user": cost_by_user,
            "cost_by_agent": cost_by_agent,
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


