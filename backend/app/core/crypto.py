"""Criptografia simétrica (Fernet) para senhas armazenadas no banco."""

from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings


class CryptoError(Exception):
    """Falha ao criptografar ou descriptografar um valor."""


def _fernet() -> Fernet:
    key = get_settings().encryption_key.strip()
    if not key:
        msg = (
            "ENCRYPTION_KEY não configurada. "
            "Gere com: python -c \"from cryptography.fernet import Fernet; "
            "print(Fernet.generate_key().decode())\""
        )
        raise CryptoError(msg)
    try:
        return Fernet(key.encode("utf-8"))
    except (ValueError, TypeError) as exc:
        raise CryptoError("ENCRYPTION_KEY inválida (não é uma chave Fernet válida)") from exc


def encrypt(plaintext: str) -> str:
    """Criptografa texto em claro e retorna token Fernet (str)."""
    return _fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt(token: str) -> str:
    """Descriptografa token Fernet para texto em claro."""
    try:
        return _fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise CryptoError("Falha ao descriptografar: token inválido ou chave errada") from exc
