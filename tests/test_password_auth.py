import pytest
from fastapi.testclient import TestClient
from nexusai.api.server import app

client = TestClient(app)

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
