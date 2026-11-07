import os
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "EduGrade API"
    app_version: str = "1.0.0"
    database_url: str = Field(default="sqlite+aiosqlite:///./edugrade.db")
    secret_key: str = Field(default="edugrade_super_secure_secret_jwt_key_2026_academic_cloud")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=1440)
    environment: str = Field(default="development")
    cors_origins: list[str] = Field(default=["*"])

    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        if isinstance(v, str):
            if v.startswith("postgres://"):
                v = v.replace("postgres://", "postgresql+asyncpg://", 1)
            elif v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
                v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
