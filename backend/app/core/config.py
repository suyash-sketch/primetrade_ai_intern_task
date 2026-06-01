from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_core.core_schema import ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME : str = "PrimeTradeAI Intern Task"
    API_V1_STR : str = "/api/v1"
    DEBUG : bool = False

    # ── Security & Authentication (JWT) ──────────
    SECRET_KEY: str 
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ── Database (PostgreSQL) ────────────────────
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: str = "5432"

    DATABASE_URL: str | None = None


    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v : str | None, info : ValidationInfo) -> str:
        if isinstance(v, str):
            return v
        
        return (
            f"postgresql://{info.data['POSTGRES_USER']}:{info.data['POSTGRES_PASSWORD']}"
            f"@{info.data["POSTGRES_SERVER"]}:{info.data['POSTGRES_PORT']}"
            f"/{info.data['POSTGRES_DB']}"
        )
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v : Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list) or isinstance(v, str):
            return v
        raise ValueError("Invalid CORS origins format.")
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()