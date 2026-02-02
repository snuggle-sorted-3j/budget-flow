from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os

class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "BudgetFlow"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"

    # Read from environment - NO hardcoded password
    DATABASE_URL: str
    
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:8050"]

settings = Settings()
