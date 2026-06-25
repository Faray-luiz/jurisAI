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
    # Fallback to simulated session tokens (like 'lucas@jurisai.com.br') if it is an email
    if "@" in token:
        if settings.ENV == "production":
            raise HTTPException(status_code=401, detail="Tokens simulados não são permitidos em produção.")
        return {
            "email": token,
            "name": token.split("@")[0].replace(".com", "").replace(".br", "").capitalize(),
            "verified": True
        }

    if settings.GOOGLE_CLIENT_ID:
        try:
            # Fetch Google's JWKS to decode and check signature
            jwks_url = "https://www.googleapis.com/oauth2/v3/certs"
            jwks_client = PyJWKClient(jwks_url)
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=settings.GOOGLE_CLIENT_ID,
                issuer="https://accounts.google.com"
            )
            
            return {
                "email": payload.get("email"),
                "name": payload.get("name", "Advogado Google"),
                "verified": payload.get("email_verified", False)
            }
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Token do Google inválido: {str(e)}")
    else:
        if settings.ENV == "production":
            raise HTTPException(status_code=401, detail="Autenticação Google não configurada no servidor de produção.")
            
        # Development / Simulation mode: Decode JWT without signature check
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

def verify_microsoft_token(token: str) -> dict:
    """
    Decodes and validates a Microsoft Entra ID (M365) JWT ID Token.
    Validates against Microsoft's common JWKS endpoint if MICROSOFT_CLIENT_ID is set.
    """
    if "@" in token:
        if settings.ENV == "production":
            raise HTTPException(status_code=401, detail="Tokens simulados não são permitidos em produção.")
        return {
            "email": token,
            "name": token.split("@")[0].replace(".com", "").replace(".br", "").capitalize(),
            "verified": True
        }
        
    if settings.MICROSOFT_CLIENT_ID:
        try:
            jwks_url = "https://login.microsoftonline.com/common/discovery/v2.0/keys"
            jwks_client = PyJWKClient(jwks_url)
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=settings.MICROSOFT_CLIENT_ID,
                options={"verify_signature": True}
            )
            
            email = payload.get("preferred_username") or payload.get("email") or payload.get("upn")
            if not email:
                raise ValueError("E-mail não encontrado no token da Microsoft.")
                
            return {
                "email": email,
                "name": payload.get("name", "Advogado Microsoft"),
                "verified": True
            }
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Token da Microsoft inválido: {str(e)}")
    else:
        if settings.ENV == "production":
            raise HTTPException(status_code=401, detail="Autenticação Microsoft não configurada no servidor de produção.")
            
        # Development / Simulation mode: Decode JWT without signature check
        try:
            if token.count(".") == 2:
                payload = jwt.decode(token, options={"verify_signature": False})
                email = payload.get("preferred_username") or payload.get("email") or payload.get("upn")
                return {
                    "email": email,
                    "name": payload.get("name", "Usuário Microsoft"),
                    "verified": True
                }
        except Exception:
            pass
            
        return {
            "email": token,
            "name": token.split("@")[0].replace(".com", "").replace(".br", "").capitalize(),
            "verified": True
        }

def get_current_user(token: str = Depends(api_key_header)) -> dict:
    if not token:
        raise HTTPException(status_code=401, detail="Token de autorização ausente.")
    
    raw_token = token.replace("Bearer ", "").strip()
    
    iss = None
    if raw_token.count(".") == 2:
        try:
            unverified_payload = jwt.decode(raw_token, options={"verify_signature": False})
            iss = unverified_payload.get("iss", "")
        except Exception:
            pass
            
    profile = None
    if iss and ("microsoft" in iss.lower() or "windows.net" in iss.lower() or "login.microsoftonline" in iss.lower()):
        profile = verify_microsoft_token(raw_token)
    elif iss and "accounts.google.com" in iss.lower():
        profile = verify_google_token(raw_token)
    else:
        try:
            profile = verify_google_token(raw_token)
        except HTTPException as he:
            if "não são permitidos" in he.detail or "não configurada" in he.detail:
                raise he
            try:
                profile = verify_microsoft_token(raw_token)
            except Exception:
                raise he
        except Exception:
            try:
                profile = verify_microsoft_token(raw_token)
            except HTTPException as he2:
                if "não são permitidos" in he2.detail or "não configurada" in he2.detail:
                    raise he2
                raise HTTPException(status_code=401, detail="Token de autenticação inválido.")
            except Exception:
                raise HTTPException(status_code=401, detail="Token de autenticação inválido.")
                
    if not profile or not profile.get("email"):
        raise HTTPException(status_code=401, detail="Token de autenticação não contém e-mail válido.")
        
    email = profile["email"]
    user = get_db_user(email)
    if user:
        return user
        
    raise HTTPException(status_code=401, detail="Acesso negado: Usuário não cadastrado na plataforma.")

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
