import pytest
from fastapi.testclient import TestClient
from nexusai.api.server import app

client = TestClient(app)

@pytest.fixture(autouse=True, scope="module")
def setup_test_users():
    """Ensure test users exist in database before running authentication tests."""
    client.post("/api/auth/signup", json={"email": "admin@nexusai.com", "password": "Admin@123"})
    client.post("/api/auth/signup", json={"email": "prasannamadiwar71@gmail.com", "password": "Prasanna@123"})

def test_login_success_with_correct_password():
    """Verify that a user with the correct password can log in."""
    res = client.post("/api/auth/login", json={
        "email": "admin@nexusai.com",
        "password": "Admin@123"
    })
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "admin@nexusai.com"


def test_login_success_user_account():
    """Verify user prasannamadiwar71@gmail.com with correct password logs in."""
    res = client.post("/api/auth/login", json={
        "email": "prasannamadiwar71@gmail.com",
        "password": "Prasanna@123"
    })
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "prasannamadiwar71@gmail.com"


def test_login_rejected_with_incorrect_password():
    """Verify that any user with an incorrect password is strictly rejected with 401."""
    res = client.post("/api/auth/login", json={
        "email": "admin@nexusai.com",
        "password": "WrongPassword999!"
    })
    assert res.status_code == 401
    assert "Incorrect password" in res.json().get("detail", "")


def test_login_rejected_for_unregistered_user():
    """Verify that unregistered users cannot log in and receive 401."""
    res = client.post("/api/auth/login", json={
        "email": "unregistered_random_user_99@nexusai.com",
        "password": "RandomPassword@123"
    })
    assert res.status_code == 401
    assert "not registered in the database" in res.json().get("detail", "")


def test_login_rejected_for_empty_password():
    """Verify that an empty password is rejected with 400."""
    res = client.post("/api/auth/login", json={
        "email": "admin@nexusai.com",
        "password": ""
    })
    assert res.status_code == 400


def test_random_salt_generation_and_verification():
    """Verify that each hash has a unique random 16-byte salt, yet verifies correctly."""
    from nexusai.db.auth import hash_password, verify_password
    pwd = "MySecretPassword@2026"
    hash1 = hash_password(pwd)
    hash2 = hash_password(pwd)

    # Different salts must yield different stored strings
    assert hash1 != hash2
    assert "$" in hash1
    assert "$" in hash2

    salt1, key1 = hash1.split("$", 1)
    salt2, key2 = hash2.split("$", 1)
    assert len(bytes.fromhex(salt1)) == 16
    assert len(bytes.fromhex(salt2)) == 16
    assert salt1 != salt2

    # Both must verify successfully
    assert verify_password(pwd, hash1) is True
    assert verify_password(pwd, hash2) is True
    assert verify_password("WrongPassword!", hash1) is False
    assert verify_password("WrongPassword!", hash2) is False


def test_legacy_salt_verification_fallback():
    """Verify that legacy hashes without '$' continue to verify via legacy-salt fallback."""
    import hashlib
    from nexusai.db.auth import LEGACY_SALT, verify_password
    pwd = "LegacyUserSecret#123"

    # Compute raw legacy hash without salt prefix
    legacy_key = hashlib.pbkdf2_hmac("sha256", pwd.encode("utf-8"), LEGACY_SALT, 100000).hex()
    assert "$" not in legacy_key

    # Must verify correctly using legacy fallback
    assert verify_password(pwd, legacy_key) is True
    # Incorrect password must be rejected
    assert verify_password("DifferentPassword", legacy_key) is False


def test_malformed_and_empty_hash_handling():
    """Verify edge cases like empty string or malformed hashes return False safely."""
    from nexusai.db.auth import verify_password
    assert verify_password("", "somehash") is False
    assert verify_password("pwd", "") is False
    assert verify_password("pwd", "not_valid_hex$not_valid_hex") is False
    assert verify_password("pwd", "invalid") is False
