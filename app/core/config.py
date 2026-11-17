from collections import Counter
from functools import lru_cache
from math import log2

from pydantic import EmailStr, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def is_adequate_production_secret(value: str) -> bool:
    """Reject obvious weak keys; heuristics cannot prove cryptographic entropy."""
    if len(value) < 32 or any(char.isspace() for char in value):
        return False
    counts = Counter(value)
    if len(counts) < 12:
        return False
    entropy = -sum((count / len(value)) * log2(count / len(value)) for count in counts.values())
    if entropy < 3.5:
        return False
    normalized = "".join(char for char in value.casefold() if char.isalnum())
    placeholders = (
        "troquepor",
        "changeme",
        "replaceme",
        "yoursecret",
        "testsecret",
        "cisecret",
        "productionsecret",
        "developmentsecret",
        "secretkey",
        "jwtsecret",
        "password",
        "senhasecreta",
        "correcthorsebatterystaple",
    )
    if any(marker in normalized for marker in placeholders):
        return False
    if value in (value + value)[1:-1]:
        return False  # A shorter sequence repeated to reach the required length.
    for sequence in ("0123456789", "abcdefghijklmnopqrstuvwxyz", "qwertyuiopasdfghjklzxcvbnm"):
        for direction in (sequence, sequence[::-1]):
            if normalized in direction * (len(normalized) // len(direction) + 2):
                return False
    return True


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", hide_input_in_errors=True)

    app_name: str = "EduTrack AI"
    environment: str = "development"
    database_url: str
    test_database_url: str | None = None
    jwt_secret: str = Field(repr=False)
    jwt_expire_minutes: int = 60
    password_reset_minutes: int = 30
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: EmailStr
    smtp_password: str
    smtp_from_email: EmailStr
    frontend_url: str = "http://127.0.0.1:8000"
    cookie_secure: bool = False
    google_classroom_enabled: bool = False
    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_oauth_redirect_uri: str = "http://127.0.0.1:8000/api/integrations/classroom/callback"
    google_token_encryption_key: str | None = None
    edu_ai_enabled: bool = False
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.5-flash"
    edu_ai_requests_per_minute: int = 5
    edu_ai_requests_per_day: int = 50
    demo_email: EmailStr = "demo@example.com"
    demo_password: str = "Demo-Segura-123"

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.google_classroom_enabled and not all(
            (
                self.google_client_id,
                self.google_client_secret,
                self.google_token_encryption_key,
            )
        ):
            raise ValueError("A configuração do Google Classroom está incompleta.")

        if self.edu_ai_enabled and not self.gemini_api_key:
            raise ValueError("A configuração do EDU IA está incompleta.")

        if self.environment.strip().casefold() == "production":
            if not is_adequate_production_secret(self.jwt_secret):
                raise ValueError(
                    "JWT_SECRET inadequado para produção. Configure um segredo gerado "
                    "criptograficamente (32 bytes aleatórios), sem exemplos ou padrões previsíveis."
                )
            if not self.cookie_secure:
                raise ValueError("COOKIE_SECURE deve ser true em produção.")
            if not self.frontend_url.startswith("https://"):
                raise ValueError("FRONTEND_URL deve usar HTTPS em produção.")
            if self.google_classroom_enabled and not self.google_oauth_redirect_uri.startswith(
                "https://"
            ):
                raise ValueError("GOOGLE_OAUTH_REDIRECT_URI deve usar HTTPS em produção.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
