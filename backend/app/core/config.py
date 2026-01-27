"""
Application Configuration
Manages all environment variables and app settings
"""
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # App Settings
    APP_NAME: str = "AgentBuilder"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # MongoDB
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "agentbuilder"
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    
    # Google Gemini
    GEMINI_API_KEY: Optional[str] = None
    
    # Anthropic (optional)
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # GROQ (fast inference)
    GROQ_API_KEY: Optional[str] = None
    
    # Model Settings - Default to Gemini if available
    DEFAULT_MODEL: str = "gemini-1.5-flash"
    DEFAULT_TEMPERATURE: float = 0.7
    
    # Supported Models by Provider
    OPENAI_MODELS: list[str] = ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini"]
    GEMINI_MODELS: list[str] = ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro", "gemini-2.0-flash-exp"]
    GROQ_MODELS: list[str] = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "llama-3.1-70b-versatile", "mixtral-8x7b-32768"]
    
    # ChromaDB for RAG
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    
    # Execution Settings
    MAX_EXECUTION_TIME: int = 300  # seconds
    MAX_RETRIES: int = 3
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
