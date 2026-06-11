from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "SecureMAX API"
    environment: str = "development"
    api_prefix: str = "/api"
    backend_cors_origins: list[str] | str = Field(default_factory=lambda: ["http://localhost:5173"])

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "securemax_siniestros"

    auth_required: bool = False
    jwt_secret_key: str = "change-me-use-a-long-random-secret"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    upload_max_total_bytes: int = 20 * 1024 * 1024
    upload_allowed_extensions: list[str] | str = Field(default_factory=lambda: ["pdf", "csv", "xlsx", "json", "png", "jpg", "jpeg", "txt"])
    upload_local_dir: Path = Path("storage/uploads")

    default_admin_email: str = "admin@example.com"
    default_admin_password: str = "change-me"
    default_admin_full_name: str = "SecureMAX Admin"

    openai_api_key: str | None = None
    openai_model: str = "gpt-3.5-turbo"
    openai_temperature: float = 0.1
    chroma_collection: str = "securemax_documents"

    @field_validator("backend_cors_origins", "upload_allowed_extensions", mode="before")
    @classmethod
    def split_csv(cls, value: list[str] | str) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def cors_origins(self) -> list[str]:
        return list(self.backend_cors_origins)

    @property
    def allowed_extensions(self) -> set[str]:
        return {item.lower().lstrip(".") for item in self.upload_allowed_extensions}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
