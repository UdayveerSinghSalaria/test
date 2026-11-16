from cryptography.fernet import Fernet
from app.config import settings

_fernet = Fernet(settings.FERNET_KEY.encode())


def encrypt(data: str) -> str:
    """Encrypt a string using Fernet."""
    return _fernet.encrypt(data.encode()).decode()


def decrypt(encrypted_data: str) -> str:
    """Decrypt a Fernet-encrypted string."""
    return _fernet.decrypt(encrypted_data.encode()).decode()