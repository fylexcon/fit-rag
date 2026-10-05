from cryptography.fernet import Fernet
from core.config import settings

# This key must be a URL-safe base64-encoded 32-byte key.
fernet = Fernet(settings.HUAWEI_ENCRYPTION_KEY.encode())

def encrypt_token(token: str) -> str:
    """Encrypts a string (e.g. access_token or refresh_token)."""
    return fernet.encrypt(token.encode()).decode()

def decrypt_token(encrypted_token: str) -> str:
    """Decrypts a previously encrypted token string."""
    return fernet.decrypt(encrypted_token.encode()).decode()
