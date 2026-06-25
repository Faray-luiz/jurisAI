import base64
import hashlib
from cryptography.fernet import Fernet
from backend.app.core.config import settings

def _get_fernet_key() -> bytes:
    """
    Derives a valid 32-byte URL-safe base64 key deterministically from settings.JWT_SECRET.
    """
    secret_bytes = settings.JWT_SECRET.encode("utf-8")
    key_32 = hashlib.sha256(secret_bytes).digest()
    return base64.urlsafe_b64encode(key_32)

def encrypt_text(text: str) -> str:
    """
    Encrypts plain text using AES-128/256 (Fernet) and returns a base64 encoded string.
    """
    if not text:
        return ""
    key = _get_fernet_key()
    fernet = Fernet(key)
    encrypted_bytes = fernet.encrypt(text.encode("utf-8"))
    return encrypted_bytes.decode("utf-8")

def decrypt_text(encrypted_base64: str) -> str:
    """
    Decrypts a base64 Fernet encrypted string and returns the original plain text.
    """
    if not encrypted_base64:
        return ""
    key = _get_fernet_key()
    fernet = Fernet(key)
    decrypted_bytes = fernet.decrypt(encrypted_base64.encode("utf-8"))
    return decrypted_bytes.decode("utf-8")
