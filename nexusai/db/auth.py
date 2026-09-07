"""
Authentication and Password Hashing Helpers for NexusAI.
Uses PBKDF2-HMAC-SHA256 for secure salted password storage.
"""
import hashlib

SALT = b"nexusai_secure_salt_v2"


def hash_password(password: str) -> str:
    """Hash a plaintext password using PBKDF2-HMAC-SHA256."""
    if not password:
        return ""
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), SALT, 100000)
    return key.hex()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify that a plaintext password matches the stored hash."""
    if not plain_password or not hashed_password:
        return False
    return hash_password(plain_password) == hashed_password
