from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # OpenAI Configuration
    openai_api_key: str
    openai_base_url: str = "https://api.openai.com/v1"
    openai_chat_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    
    # Database
    db_url: str = "sqlite:///./app.db"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_recycle: int = 3600
    
    # API Security
    api_key: str
    
    # RAG Configuration
    rag_top_k: int = 6
    
    # CORS
    allowed_origin: str = "http://localhost:8000"
    
    # Rate Limiting
    redis_url: str = "redis://localhost:6379"
    rate_limit_enabled: bool = True
    
    # Debug
    debug: bool = False

    class Config:
        env_file = ".env"

settings = Settings()