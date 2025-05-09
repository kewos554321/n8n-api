from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    # API 設置
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "N8N API"
    
    # CORS 設置
    BACKEND_CORS_ORIGINS: list = ["*"]
    
    # N8N 設置
    N8N_API_URL: Optional[str] = None
    N8N_API_KEY: Optional[str] = None

    # Yahoo Finance 設置
    YAHOO_FINANCE_CACHE_EXPIRY: int = 3600  # 快取過期時間（秒）

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings() 