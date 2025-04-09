from pydantic_settings import BaseSettings

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
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings() 