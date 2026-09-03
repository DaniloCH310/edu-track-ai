from cryptography.fernet import Fernet, InvalidToken

INVALID_KEY_MESSAGE = "GOOGLE_TOKEN_ENCRYPTION_KEY não é uma chave Fernet válida."
INVALID_TOKEN_MESSAGE = "O token do Google Classroom não pôde ser decifrado."


def _fernet(key: str) -> Fernet:
    try:
        return Fernet(key.encode("ascii"))
    except (ValueError, TypeError, UnicodeEncodeError) as exception:
        raise ValueError(INVALID_KEY_MESSAGE) from exception


def encrypt_refresh_token(token: str, key: str) -> str:
    try:
        return _fernet(key).encrypt(token.encode("utf-8")).decode("ascii")
    except (TypeError, UnicodeEncodeError) as exception:
        raise ValueError("O refresh token informado é inválido.") from exception


def decrypt_refresh_token(ciphertext: str, key: str) -> str:
    try:
        return _fernet(key).decrypt(ciphertext.encode("ascii")).decode("utf-8")
    except (InvalidToken, TypeError, UnicodeError) as exception:
        raise ValueError(INVALID_TOKEN_MESSAGE) from exception
