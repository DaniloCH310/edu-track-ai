from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def validate_strong_password(password: str) -> str:
    if len(password) < 10:
        raise ValueError("A senha deve ter pelo menos 10 caracteres.")
    if not any(character.isupper() for character in password):
        raise ValueError("A senha deve conter uma letra maiúscula.")
    if not any(character.islower() for character in password):
        raise ValueError("A senha deve conter uma letra minúscula.")
    if not any(character.isdigit() for character in password):
        raise ValueError("A senha deve conter um número.")
    return password


class RegisterInput(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str

    @field_validator("name", mode="before")
    @classmethod
    def trim_name(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        return validate_strong_password(value)


class LoginInput(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        return value.strip().lower() if isinstance(value, str) else value


class ForgotPasswordInput(BaseModel):
    email: EmailStr

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        return value.strip().lower() if isinstance(value, str) else value


class ResetPasswordInput(BaseModel):
    token: str = Field(min_length=16, max_length=200)
    new_password: str

    @field_validator("new_password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        return validate_strong_password(value)


class UserOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: EmailStr


class MessageOutput(BaseModel):
    message: str
