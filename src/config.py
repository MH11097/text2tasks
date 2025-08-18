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
    
    # API Security
    api_key: str
    
    # RAG Configuration
    rag_top_k: int = 6
    
    # CORS
    allowed_origin: str = "http://localhost:8000"
    
    # Debug
    debug: bool = False

    class Config:
        env_file = ".env"

settings = Settings()