from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings."""
    PROJECT_NAME: str = "Jonas Backend"
    PROJECT_DESCRIPTION: str = "Backend for the project"
    PROJECT_VERSION: str = "1.0.0"
    PRODUCTION: bool = False
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    
    # API Settings
    API_URL: str = "http://localhost:8000"
    API_PREFIX: str = "/api"
    API_VERSION_PREFIX: str = "/v1"

    # Google AI API Settings
    GOOGLE_API_KEY: str = "AIzaSyB0000000000000000000000000000000"
    AI_AGENT_MODEL: str = "gemini-2.5-pro-preview-03-25"
    BROWSER_EXECUTION_MODEL: str = "gemini-2.0-flash"
    BROWSER_PLANNER_MODEL: str = "gemini-1.5-flash"

    # MongoDB Atlas Settings
    MONGODB_URL: str = "connection_string"
    MONGODB_DB_NAME: str = "DB_NAME"

    # FH Settings
    FH_HOST: str = "localhost"
    FH_PORT: int = 6969
    FH_USER: str = "root"
    FH_PASSWORD: str = "root"
    FH_DB_NAME: str = "test"
    FH_SQL_POOL_SIZE: int = 5
    FH_SQL_MAX_OVERFLOW: int = 10
    FH_SQL_ECHO: bool = True

    # Redis Settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # Security
    # Generate a secure secret key: `openssl rand -hex 32`
    SECRET_KEY: str = "secret_key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 11520  # 8 days
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    SIGNUP_TOKEN_EXPIRE_MINUTES: int = 10

    JWT_SECRET_KEY: str = "your-super-secret-key-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- Agent Settings --- #

    # --- Credentials --- #
    TRELLO_USERNAME: Optional[str] = None
    TRELLO_PASSWORD: Optional[str] = None
    TRELLO_TOTP_SECRET: Optional[str] = None      # Secret key for TOTP generation

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = True

settings = Settings() 