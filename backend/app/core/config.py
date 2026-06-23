import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from typing import Dict, Any

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "JurisAI Gateway"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./jurisai.db")
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "*")
    
    JWT_SECRET: str = os.getenv("JWT_SECRET", "super-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week
    
    # Model APIs
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "mock-openai-key")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "mock-anthropic-key")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "mock-gemini-key")
    
    # Cost per 1k tokens (input, output) in USD
    # As per PRD selection
    MODEL_PRICING: Dict[str, Dict[str, float]] = {
        "gpt-4o-mini": {"input": 0.000150, "output": 0.000600},
        "gpt-4o": {"input": 0.002500, "output": 0.010000},
        "claude-3-5-sonnet": {"input": 0.003000, "output": 0.015000},
        "claude-3-opus": {"input": 0.015000, "output": 0.075000},
        "gemini-1.5-pro": {"input": 0.001250, "output": 0.005000},
        "gemini-1.5-flash": {"input": 0.000075, "output": 0.000300}
    }
    
    class Config:
        case_sensitive = True

settings = Settings()
