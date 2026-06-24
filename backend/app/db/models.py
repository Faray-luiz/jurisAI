import time
import json
from sqlalchemy import Column, Integer, String, Float, Text, Boolean, create_engine
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class DBUser(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False) # Sócio, Advogado, Compliance, TI
    quota_limit = Column(Float, default=50.0)
    quota_spent = Column(Float, default=0.0)
    _assigned_clients = Column(Text, default="[]") # JSON list
    _conflicted_clients = Column(Text, default="[]") # JSON list
    # Invitation / onboarding fields
    invitation_token = Column(String, nullable=True)        # UUID v4 (expires in 72h)
    invitation_sent_at = Column(Float, nullable=True)       # unix timestamp
    invitation_accepted = Column(Boolean, default=False)    # True after password set
    password_hash = Column(String, nullable=True)           # bcrypt hash

    @property
    def assigned_clients(self):
        try:
            return json.loads(self._assigned_clients)
        except Exception:
            return []

    @assigned_clients.setter
    def assigned_clients(self, value):
        self._assigned_clients = json.dumps(value)

    @property
    def conflicted_clients(self):
        try:
            return json.loads(self._conflicted_clients)
        except Exception:
            return []

    @conflicted_clients.setter
    def conflicted_clients(self, value):
        self._conflicted_clients = json.dumps(value)


class DBProcess(Base):
    __tablename__ = "processes"
    
    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    process_number = Column(String, nullable=False)
    client = Column(String, index=True, nullable=False)
    matter = Column(String, nullable=False)


class DBAuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(Float, default=time.time)
    user_email = Column(String, nullable=False)
    action = Column(String, nullable=False)
    process_id = Column(String, default="N/A")
    model = Column(String, nullable=False)
    cost_usd = Column(Float, default=0.0)
    status = Column(String, nullable=False)
    prompt_masked = Column(Text, nullable=False)
    response_masked = Column(Text, nullable=False)
    grounding_status = Column(String, nullable=False)


class DBAgentConfig(Base):
    __tablename__ = "agent_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    task_type = Column(String, unique=True, index=True, nullable=False) # analise_peticao, rascunho_recurso, default
    provider = Column(String, nullable=False) # openai, anthropic, google
    model = Column(String, nullable=False)
    temperature = Column(Float, default=0.0)
    system_prompt = Column(Text, nullable=False)


class DBGroundingDoc(Base):
    __tablename__ = "grounding_docs"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False) # art 186 cc
    citation = Column(String, nullable=False) # Art. 186 do Código Civil
    text = Column(Text, nullable=False)
    source = Column(String, nullable=False) # LexML - Código Civil
    is_active = Column(Boolean, default=True)
    agent_task_type = Column(String, nullable=True, default="global") # analise_peticao, rascunho_recurso, global, etc.



class DBSystemSetting(Base):
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    value = Column(String, nullable=False)


class DBMission(Base):
    __tablename__ = "missions"

    id = Column(Integer, primary_key=True, index=True)
    task_type = Column(String, unique=True, index=True, nullable=False)  # slug, ex: contrato_revisao
    display_name = Column(String, nullable=False)                         # ex: Revisão de Contratos
    icon = Column(String, nullable=False, default="⚖️")                 # emoji
    description = Column(String, nullable=False, default="")             # subtexto do card
    default_prompt = Column(Text, nullable=False, default="")            # prompt pré-preenchido ao clicar
    is_active = Column(Boolean, default=True)
    created_at = Column(Float, default=time.time)
