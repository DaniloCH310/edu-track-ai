from functools import lru_cache

from pydantic import EmailStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "EduTrack AI"
    environment: str = "development"
    database_url: str
    test_database_url: str | None = None
    jwt_secret: str
    jwt_expire_minutes: int = 60
    password_reset_minutes: int = 30
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: EmailStr
    smtp_password: str
    smtp_from_email: EmailStr
    frontend_url: str = "http://127.0.0.1:8000"
    cookie_secure: bool = False
    demo_email: EmailStr = "demo@example.com"
    demo_password: str = "Demo-Segura-123"

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.environment.casefold() != "production":
            return self

        if not self.cookie_secure:
            raise ValueError("COOKIE_SECURE deve ser true em produção.")
        if not self.frontend_url.startswith("https://"):
            raise ValueError("FRONTEND_URL deve usar HTTPS em produção.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
