"""Credential encryption — Fernet symmetric encryption for OAuth tokens.

The key lives ONLY in backend environment variables. Nothing here ever logs
key material or plaintext tokens.
"""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from ..config import get_settings

_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        key = get_settings().credentials_encryption_key
        if not key:
            raise RuntimeError(
                "CREDENTIALS_ENCRYPTION_KEY is not configured; refusing to "
                "handle OAuth credentials in plaintext."
            )
        _fernet = Fernet(key.encode())
    return _fernet


def encrypt(value: str) -> str:
    """Encrypt a secret for database storage."""
    if not value:
        return ""
    return _get_fernet().encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    """Decrypt a stored secret. Raises InvalidToken if tampered/wrong key."""
    if not value:
        return ""
    try:
        return _get_fernet().decrypt(value.encode()).decode()
    except InvalidToken as exc:
        raise ValueError(
            "Stored credential could not be decrypted (wrong or rotated "
            "CREDENTIALS_ENCRYPTION_KEY). Reconnect the integration."
        ) from exc
