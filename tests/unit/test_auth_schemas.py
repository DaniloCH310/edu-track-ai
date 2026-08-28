import pytest
from pydantic import ValidationError

from app.schemas.auth import RegisterInput, ResetPasswordInput


@pytest.mark.parametrize(
    "password",
    [
        "Curta-1",
        "sem-maiuscula-123",
        "SEM-MINUSCULA-123",
        "SemNumeroAlgum",
    ],
)
def test_registration_rejects_passwords_missing_a_strength_requirement(password):
    """Catches accepting a password that misses one approved minimum requirement."""
    with pytest.raises(ValidationError):
        RegisterInput(name="Ana", email="ana@example.com", password=password)


def test_registration_trims_identity_fields_and_accepts_strong_password():
    """Catches storing accidental surrounding whitespace in names and emails."""
    payload = RegisterInput(
        name="  Ana Estudante  ",
        email="  ANA@example.com  ",
        password="Senha-Forte-123",
    )

    assert payload.name == "Ana Estudante"
    assert payload.email == "ana@example.com"


def test_reset_password_uses_the_same_strength_policy():
    """Catches password reset bypassing the registration strength policy."""
    with pytest.raises(ValidationError):
        ResetPasswordInput(token="token-valido", new_password="fraca")
