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
    AI_API_KEY: str = "AIzaSyB0000000000000000000000000000000"
    AI_MODEL: str = "gemini-2.0-flash"

    # MongoDB Atlas Settings
    MONGODB_URL: str = "connection_string"
    MONGODB_DB_NAME: str = "DB_NAME"

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

    # OpenAI API Key (add this)
    OPENAI_API_KEY: str = "YOUR_OPENAI_API_KEY_HERE" # Replace with actual key or env variable loading

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