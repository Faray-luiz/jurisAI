import os
import jwt
from jwt import PyJWKClient
from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from backend.app.db.session import get_db_user, get_all_db_processes
from backend.app.core.config import settings

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

def verify_google_token(token: str) -> dict:
    """
    Decodes and validates a Google Workspace JWT ID Token.
    If GOOGLE_CLIENT_ID is set, validates against Google's JWKS endpoint.
    Otherwise, returns decoded mock/simulated payload for local testing.
    """
    if GOOGLE_CLIENT_ID:
        try:
            # Fetch Google's JWKS to decode and check signature
            jwks_url = "https://www.googleapis.com/oauth2/v3/certs"
            jwks_client = PyJWKClient(jwks_url)
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=GOOGLE_CLIENT_ID,
                issuer="https://accounts.google.com"
            )
            
            # hd (hosted domain) holds the Workspace domain name
            if payload.get("hd") != "jurisai.com.br" and not payload.get("email", "").endswith("@jurisai.com.br"):
                # Optional warning check
                pass
                
            return {
                "email": payload.get("email"),
                "name": payload.get("name", "Advogado Google"),
                "verified": payload.get("email_verified", False)
            }
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Token do Google inválido: {str(e)}")
    else:
        # Development / Simulation mode: Decode JWT without signature check
        # (or fallback to simulated session tokens like 'lucas@jurisai.com.br')
        try:
            if token.count(".") == 2:
                payload = jwt.decode(token, options={"verify_signature": False})
                return {
                    "email": payload.get("email"),
                    "name": payload.get("name", "Usuário Google"),
                    "verified": True
                }
        except Exception:
            pass
            
        # Fallback to simulated email bearer string
        return {
            "email": token,
            "name": token.split("@")[0].replace(".com", "").replace(".br", "").capitalize(),
            "verified": True
        }

def get_current_user(token: str = Depends(api_key_header)) -> dict:
    if not token:
        # Default to Lucas for local validation convenience if header is missing
        return get_db_user("lucas@jurisai.com.br")
    
    raw_token = token.replace("Bearer ", "").strip()
    
    # Verify Google Workspace Token
    google_profile = verify_google_token(raw_token)
    email = google_profile["email"]
    
    user = get_db_user(email)
    if user:
        return user
        
    # Auto onboarding for new Google Workspace users
    from backend.app.db.session import SessionLocal
    from backend.app.db.models import DBUser
    
    db = SessionLocal()
    try:
        new_user = DBUser(
            email=email,
            name=google_profile["name"],
            role="Advogado",
            quota_limit=50.0,
            quota_spent=0.0,
            assigned_clients=["Companhia Gama"],
            conflicted_clients=[]
        )
        db.add(new_user)
        db.commit()
        
        # return user dict
        return get_db_user(email)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=401, detail=f"Erro no auto-cadastro de usuário do Google Workspace: {e}")
    finally:
        db.close()

def verify_process_access(process_id: str, user: dict = Depends(get_current_user)) -> dict:
    # Find the process in DB
    processes = get_all_db_processes()
    process = next((p for p in processes if p["id"] == process_id), None)
    if not process:
        raise HTTPException(status_code=444, detail="Processo não encontrado.")
    
    # Check Ethical Wall constraints
    client = process["client"]
    if client in user.get("conflicted_clients", []):
        raise HTTPException(
            status_code=403, 
            detail=f"Bloqueio de Muralha Ética: Usuário não tem permissão para acessar dados do cliente {client}."
        )
    
    # Check RBAC permissions: Compliance and TI can review configuration/audits, but cannot read processes
    if user["role"] in ["Compliance", "TI"] and not user.get("assigned_clients"):
        raise HTTPException(
            status_code=403,
            detail="Seu perfil de governança/TI não permite acesso direto a processos de clientes."
        )
        
    return process
