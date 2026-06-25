import time
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from backend.app.db.models import Base, DBUser, DBProcess, DBAuditLog, DBAgentConfig, DBGroundingDoc, DBSystemSetting, DBMission, DBProcessDocument
from backend.app.core.config import settings
import os

DATABASE_URL = settings.DATABASE_URL
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Thread-safe connection for SQLite in FastAPI
is_sqlite = DATABASE_URL.startswith("sqlite")
if is_sqlite:
    db_path = DATABASE_URL.replace("sqlite:///", "").replace("sqlite://", "")
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        try:
            os.makedirs(db_dir, exist_ok=True)
        except Exception as e:
            print(f"Error creating database directory {db_dir}: {e}")

connect_args = {"check_same_thread": False} if is_sqlite else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

# Defensively add agent_task_type to grounding_docs for SQLite/Postgres in case table exists
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE grounding_docs ADD COLUMN agent_task_type VARCHAR DEFAULT 'global'"))
        conn.commit()
    except Exception:
        pass

# Defensively add embedding_json to grounding_docs
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE grounding_docs ADD COLUMN embedding_json TEXT"))
        conn.commit()
    except Exception:
        pass

# Defensively add invitation / password columns to users table
_user_migrations = [
    "ALTER TABLE users ADD COLUMN invitation_token VARCHAR",
    "ALTER TABLE users ADD COLUMN invitation_sent_at FLOAT",
    "ALTER TABLE users ADD COLUMN invitation_accepted BOOLEAN DEFAULT FALSE",
    "ALTER TABLE users ADD COLUMN password_hash VARCHAR",
]
for _sql in _user_migrations:
    try:
        with engine.connect() as conn:
            conn.execute(text(_sql))
            conn.commit()
    except Exception:
        pass  # Column already exists

# Seed default built-in missions if table is empty
_seed_db = SessionLocal()
try:
    if _seed_db.query(DBMission).count() == 0:
        import time as _time
        _seed_db.add_all([
            DBMission(
                task_type="analise_peticao",
                display_name="Análise de Petição Inicial",
                icon="📄",
                description="Analisa o PDF de uma petição adversária e sanitiza tentativas de injection instrução-dado.",
                default_prompt="Faça a análise completa da petição inicial em anexo. Identifique fundamentações e a adequação legal.",
                is_active=True,
                created_at=_time.time()
            ),
            DBMission(
                task_type="rascunho_recurso",
                display_name="Rascunho de Recurso",
                icon="✍️",
                description="Redige minuta de apelação sob o CPC e avalia síncronamente grounding de citações.",
                default_prompt="Elabore o rascunho de recurso contra a sentença desfavorável. Aplique a correta atribuição do ônus processual.",
                is_active=True,
                created_at=_time.time()
            ),
        ])
        _seed_db.commit()
except Exception:
    _seed_db.rollback()
finally:
    _seed_db.close()


# Helper: DB model to dictionary translation
def user_to_dict(user: DBUser) -> dict:
    if not user:
        return None
    return {
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "quota_limit": user.quota_limit,
        "quota_spent": user.quota_spent,
        "assigned_clients": user.assigned_clients,
        "conflicted_clients": user.conflicted_clients
    }

def process_to_dict(proc: DBProcess) -> dict:
    if not proc:
        return None
    return {
        "id": proc.id,
        "title": proc.title,
        "process_number": proc.process_number,
        "client": proc.client,
        "matter": proc.matter
    }

def audit_to_dict(log: DBAuditLog) -> dict:
    if not log:
        return None
    return {
        "timestamp": log.timestamp,
        "user_email": log.user_email,
        "action": log.action,
        "process_id": log.process_id,
        "model": log.model,
        "cost_usd": log.cost_usd,
        "status": log.status,
        "prompt_masked": log.prompt_masked,
        "response_masked": log.response_masked,
        "grounding_status": log.grounding_status
    }

# Pre-seed Database if empty
def seed_database():
    db = SessionLocal()
    try:
        if db.query(DBUser).count() == 0:
            print("Pre-seeding SQLite database...")
            # Seed users
            users = [
                DBUser(
                    email="lucas@jurisai.com.br",
                    name="Lucas Silva",
                    role="Advogado",
                    quota_limit=50.0,
                    quota_spent=12.45,
                    assigned_clients=["Construtora Alfa", "Companhia Gama"],
                    conflicted_clients=["Incorporadora Beta"]
                ),
                DBUser(
                    email="mariana@jurisai.com.br",
                    name="Mariana Souza",
                    role="Advogado",
                    quota_limit=50.0,
                    quota_spent=38.90,
                    assigned_clients=["Incorporadora Beta", "Companhia Gama"],
                    conflicted_clients=["Construtora Alfa"]
                ),
                DBUser(
                    email="roberto@jurisai.com.br",
                    name="Roberto Mendes",
                    role="Sócio",
                    quota_limit=500.0,
                    quota_spent=142.10,
                    assigned_clients=["Construtora Alfa", "Incorporadora Beta", "Companhia Gama"],
                    conflicted_clients=[]
                ),
                DBUser(
                    email="ana@jurisai.com.br",
                    name="Ana Rocha",
                    role="Compliance",
                    quota_limit=10.0,
                    quota_spent=0.0,
                    assigned_clients=[],
                    conflicted_clients=[]
                )
            ]
            db.add_all(users)

            # Seed processes
            processes = [
                DBProcess(
                    id="PROC-001",
                    title="Petição Inicial - Indenização",
                    process_number="1002345-12.2026.8.26.0100",
                    client="Construtora Alfa",
                    matter="Direito Imobiliário"
                ),
                DBProcess(
                    id="PROC-002",
                    title="Contestação - Cobrança Indevida",
                    process_number="2006789-98.2026.8.26.0100",
                    client="Incorporadora Beta",
                    matter="Direito Civil"
                ),
                DBProcess(
                    id="PROC-003",
                    title="Análise Contratual - Parceria",
                    process_number="0001122-45.2026.8.26.0100",
                    client="Companhia Gama",
                    matter="Direito Empresarial"
                )
            ]
            db.add_all(processes)

            # Seed default audit logs
            db.add(DBAuditLog(
                timestamp=time.time() - 3600 * 2,
                user_email="lucas@jurisai.com.br",
                action="Análise de Petição",
                process_id="PROC-001",
                model="claude-3-5-sonnet",
                cost_usd=0.045,
                status="Sucesso",
                prompt_masked="Faça a análise da petição da Construtora [REDACTED] sob a ótica do Art. 5º da CF.",
                response_masked="A petição fundamenta o direito de posse com base no [Art. 5º da CF/88]...",
                grounding_status="Verificado"
            ))
            db.add(DBAuditLog(
                timestamp=time.time() - 3600 * 1,
                user_email="mariana@jurisai.com.br",
                action="Minuta de Contestação",
                process_id="PROC-002",
                model="gpt-4o",
                cost_usd=0.120,
                status="Sucesso",
                prompt_masked="Crie rascunho de contestação para [REDACTED] usando Art. 186 do Código Civil.",
                response_masked="Fica evidente a ausência de nexo causal a ensejar reparação nos termos do [Art. 186 do Código Civil]...",
                grounding_status="Verificado"
            ))
            db.commit()
            print("SQLite Database base seed complete.")

        # Seed Agent Configs if empty
        if db.query(DBAgentConfig).count() == 0:
            print("Pre-seeding Agent Configs...")
            configs = [
                DBAgentConfig(
                    task_type="analise_peticao",
                    provider="anthropic",
                    model="claude-3-5-sonnet",
                    temperature=0.0,
                    system_prompt="Você é um assistente jurídico de alta precisão especializado em análise de petição inicial. Sempre utilize colchetes ao citar artigos específicos, ex: [Art. 186 do Código Civil]."
                ),
                DBAgentConfig(
                    task_type="rascunho_recurso",
                    provider="openai",
                    model="gpt-4o-mini",
                    temperature=0.0,
                    system_prompt="Você é um assistente jurídico de alta precisão especializado em rascunho de recurso. Sempre utilize colchetes ao citar artigos específicos, ex: [Art. 319 do CPC/2015]."
                ),
                DBAgentConfig(
                    task_type="default",
                    provider="openai",
                    model="gpt-4o-mini",
                    temperature=0.0,
                    system_prompt="Você é um assistente jurídico de alta precisão. Sempre utilize colchetes ao citar artigos específicos, ex: [Art. 5º da CF/88]."
                )
            ]
            db.add_all(configs)
            db.commit()

        # Seed Grounding Docs if empty
        if db.query(DBGroundingDoc).count() == 0:
            print("Pre-seeding Grounding Docs...")
            docs = [
                DBGroundingDoc(
                    key="art 5 cf",
                    citation="Art. 5º da CF/88",
                    text="Art. 5º Todos são iguais perante a lei, sem distinção de qualquer natureza, garantindo-se aos brasileiros e aos estrangeiros residentes no País a inviolabilidade do direito à vida, à liberdade, à igualdade, à segurança e à propriedade.",
                    source="LexML - Constituição Federal",
                    is_active=True,
                    agent_task_type="global"
                ),
                DBGroundingDoc(
                    key="art 186 cc",
                    citation="Art. 186 do Código Civil",
                    text="Art. 186. Aquele que, por ação ou omissão voluntária, negligência ou imprudência, violar direito e causar dano a outrem, ainda que exclusivamente moral, comete ato ilícito.",
                    source="LexML - Código Civil",
                    is_active=True,
                    agent_task_type="analise_peticao"
                ),
                DBGroundingDoc(
                    key="art 927 cc",
                    citation="Art. 927 do Código Civil",
                    text="Art. 927. Aquele que, por ato ilícito (arts. 186 e 187), causar dano a outrem, fica obrigado a repará-lo.",
                    source="LexML - Código Civil",
                    is_active=True,
                    agent_task_type="analise_peticao"
                ),
                DBGroundingDoc(
                    key="art 319 cpc",
                    citation="Art. 319 do CPC/2015",
                    text="Art. 319. A petição inicial indicará: I - o juízo a que é dirigida; II - os nomes, os prenomes, o estado civil, a profissão, o CPF ou o CNPJ, o endereço eletrônico e o domicílio e a residência do autor e do réu; III - os fatos e os fundamentos jurídicos do pedido...",
                    source="LexML - Código de Processo Civil",
                    is_active=True,
                    agent_task_type="rascunho_recurso"
                ),
                DBGroundingDoc(
                    key="art 373 cpc",
                    citation="Art. 373 do CPC/2015",
                    text="Art. 373. O ônus da prova incumbe: I - ao autor, quanto ao fato constitutivo de seu direito; II - ao réu, quanto à existência de fato impeditivo, modificativo ou extintivo do direito do autor.",
                    source="LexML - Código de Processo Civil",
                    is_active=True,
                    agent_task_type="rascunho_recurso"
                )
            ]
            db.add_all(docs)
            db.commit()
            print("Grounding Docs seeded successfully.")
            
        # Seed System Settings if empty
        if db.query(DBSystemSetting).count() == 0:
            print("Pre-seeding System Settings...")
            sys_settings = [
                DBSystemSetting(key="global_budget", value="15.0"),
                DBSystemSetting(key="enable_economic_routing", value="false"),
                DBSystemSetting(key="enable_global_budget", value="true"),
                DBSystemSetting(key="enable_client_billing", value="true")
            ]
            db.add_all(sys_settings)
            db.commit()
            print("System Settings seeded successfully.")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

# Run seeding
seed_database()

# Database Interface Exports
def get_db_user(email: str) -> dict:
    db = SessionLocal()
    try:
        user = db.query(DBUser).filter(DBUser.email == email).first()
        return user_to_dict(user)
    finally:
        db.close()

def get_all_db_users() -> list:
    db = SessionLocal()
    try:
        users = db.query(DBUser).all()
        return [user_to_dict(u) for u in users]
    finally:
        db.close()

def get_all_db_processes() -> list:
    db = SessionLocal()
    try:
        procs = db.query(DBProcess).all()
        return [process_to_dict(p) for p in procs]
    finally:
        db.close()

def get_all_db_audits() -> list:
    db = SessionLocal()
    try:
        audits = db.query(DBAuditLog).order_by(DBAuditLog.timestamp.desc()).all()
        return [audit_to_dict(a) for a in audits]
    finally:
        db.close()

def update_db_user_quota_limit(email: str, limit: float) -> bool:
    db = SessionLocal()
    try:
        user = db.query(DBUser).filter(DBUser.email == email).first()
        if user:
            user.quota_limit = limit
            db.commit()
            return True
        return False
    except Exception:
        db.rollback()
        return False
    finally:
        db.close()

def add_db_quota_spent(email: str, cost: float) -> bool:
    db = SessionLocal()
    try:
        user = db.query(DBUser).filter(DBUser.email == email).first()
        if user:
            user.quota_spent += cost
            db.commit()
            return True
        return False
    except Exception:
        db.rollback()
        return False
    finally:
        db.close()

def add_audit_log(user_email: str, action: str, process_id: str, model: str, cost: float, status: str, prompt: str, response: str, grounding_status: str):
    # Mask PII
    masked_prompt = prompt
    masked_response = response
    for name in ["Construtora Alfa", "Incorporadora Beta", "Companhia Gama", "Lucas Silva", "Mariana Souza"]:
        masked_prompt = masked_prompt.replace(name, "[REDACTED]")
        masked_response = masked_response.replace(name, "[REDACTED]")
        
    db = SessionLocal()
    try:
        log = DBAuditLog(
            timestamp=time.time(),
            user_email=user_email,
            action=action,
            process_id=process_id,
            model=model,
            cost_usd=cost,
            status=status,
            prompt_masked=masked_prompt,
            response_masked=masked_response,
            grounding_status=grounding_status
        )
        db.add(log)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error adding audit log: {e}")
    finally:
        db.close()

# Grounding corpus (remains a static dictionary for index reference lookup)
GROUNDING_CORPUS = {
    "art 5 cf": {
        "citation": "Art. 5º da CF/88",
        "text": "Art. 5º Todos são iguais perante a lei, sem distinção de qualquer natureza, garantindo-se aos brasileiros e aos estrangeiros residentes no País a inviolabilidade do direito à vida, à liberdade, à igualdade, à segurança e à propriedade.",
        "valid": True,
        "source": "LexML - Constituição Federal"
    },
    "art 186 cc": {
        "citation": "Art. 186 do Código Civil",
        "text": "Art. 186. Aquele que, por ação ou omissão voluntária, negligência ou imprudência, violar direito e causar dano a outrem, ainda que exclusivamente moral, comete ato ilícito.",
        "valid": True,
        "source": "LexML - Código Civil"
    },
    "art 927 cc": {
        "citation": "Art. 927 do Código Civil",
        "text": "Art. 927. Aquele que, por ato ilícito (arts. 186 e 187), causar dano a outrem, fica obrigado a repará-lo.",
        "valid": True,
        "source": "LexML - Código Civil"
    },
    "art 319 cpc": {
        "citation": "Art. 319 do CPC/2015",
        "text": "Art. 319. A petição inicial indicará: I - o juízo a que é dirigida; II - os nomes, os prenomes, o estado civil, a profissão, o CPF ou o CNPJ, o endereço eletrônico e o domicílio e a residência do autor e do réu; III - os fatos e os fundamentos jurídicos do pedido...",
        "valid": True,
        "source": "LexML - Código de Processo Civil"
    },
    "art 373 cpc": {
        "citation": "Art. 373 do CPC/2015",
        "text": "Art. 373. O ônus da prova incumbe: I - ao autor, quanto ao fato constitutivo de seu direito; II - ao réu, quanto à existência de fato impeditivo, modificativo ou extintivo do direito do autor.",
        "valid": True,
        "source": "LexML - Código de Processo Civil"
    }
}

def get_db_system_settings() -> dict:
    db = SessionLocal()
    try:
        settings_list = db.query(DBSystemSetting).all()
        s_dict = {s.key: s.value for s in settings_list}
        defaults = {
            "global_budget": "15.0",
            "enable_economic_routing": "false",
            "enable_global_budget": "true",
            "enable_client_billing": "true",
            "openai_credits_added": "5.0",
            "anthropic_credits_added": "5.0",
            "google_credits_added": "5.0"
        }
        for k, v in defaults.items():
            if k not in s_dict:
                s_dict[k] = v
        return s_dict
    except Exception:
        return {
            "global_budget": "15.0",
            "enable_economic_routing": "false",
            "enable_global_budget": "true",
            "enable_client_billing": "true",
            "openai_credits_added": "5.0",
            "anthropic_credits_added": "5.0",
            "google_credits_added": "5.0"
        }
    finally:
        db.close()

def update_db_system_setting(key: str, value: str) -> None:
    db = SessionLocal()
    try:
        setting = db.query(DBSystemSetting).filter(DBSystemSetting.key == key).first()
        if setting:
            setting.value = value
        else:
            db.add(DBSystemSetting(key=key, value=value))
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error updating system setting {key}: {e}")
    finally:
        db.close()
