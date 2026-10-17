"""
Authentication and Password Hashing Helpers for NexusAI.
Uses PBKDF2-HMAC-SHA256 with per-user random 16-byte salts and legacy fallback.
"""
import os
import hmac
import hashlib

LEGACY_SALT = b"nexusai_secure_salt_v2"
ITERATIONS = 100000


def hash_password(password: str, salt: bytes = None) -> str:
    """
    Hash a plaintext password using PBKDF2-HMAC-SHA256 with a random 16-byte salt.
    Format stored: <salt_hex>$<hash_hex>
    """
    if not password:
        return ""
    if salt is None:
        salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return f"{salt.hex()}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify that a plaintext password matches the stored hash.
    Supports both per-user random salt format (<salt_hex>$<hash_hex>)
    and legacy static salt fallback.
    """
    if not plain_password or not hashed_password:
        return False

    # Check for modern per-user salt format
    if "$" in hashed_password:
        try:
            salt_hex, key_hex = hashed_password.split("$", 1)
            salt = bytes.fromhex(salt_hex)
            computed = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, ITERATIONS)
            return hmac.compare_digest(computed.hex(), key_hex)
        except Exception:
            return False

    # Legacy-salt fallback (old 64-char hex hashes)
    try:
        legacy_key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), LEGACY_SALT, ITERATIONS)
        return hmac.compare_digest(legacy_key.hex(), hashed_password)
    except Exception:
        return False
