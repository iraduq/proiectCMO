import os
from pydantic import Field
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

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
