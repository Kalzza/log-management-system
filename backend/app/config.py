from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/logs_db"
    )
    
    # JWT
    secret_key: str = os.getenv("SECRET_KEY", "your-super-secret-key")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Syslog
    syslog_host: str = os.getenv("SYSLOG_HOST", "0.0.0.0")
    syslog_port: int = int(os.getenv("SYSLOG_PORT", "514"))
    
    # Retention
    log_retention_days: int = int(os.getenv("LOG_RETENTION_DAYS", "7"))
    
    # Debug
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()
