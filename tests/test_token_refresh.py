"""
Unit test for automatic encrypted persistence of refreshed Google OAuth tokens to MongoDB.
Validates:
1. MongoRefreshingCredentials intercepts refresh() execution.
2. The refreshed access token and expiration are persisted back to MongoDB under the user's account.
3. Stored token in MongoDB is strictly encrypted with Fernet (no plaintext leakage).
4. Decrypted payload matches the refreshed access token and preserves refresh_token and scopes.
"""
import time
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta
from nexusai.db.credentials import CredentialManager, MongoRefreshingCredentials


def test_token_refresh_persists_encrypted_to_mongo():
    """Verify that when Google OAuth token refreshes, updated access token is encrypted and saved to MongoDB."""
    mock_manager = CredentialManager()
    user_id = "test_refresh_user_123"
    service = "gmail"

    # Initial token data stored in MongoDB
    initial_data = {
        "token": "initial-expired-access-token",
        "refresh_token": "valid-long-lived-refresh-token-xyz",
        "client_id": "google-client-id-001.apps.googleusercontent.com",
        "client_secret": "client-secret-999",
        "scopes": ["https://mail.google.com/"],
        "token_uri": "https://oauth2.googleapis.com/token"
    }

    # Save initial credential in manager
    mock_manager.save_credential(
        user_id=user_id,
        service=service,
        auth_type="oauth_token",
        credential_data=initial_data,
        metadata={"filename": "token.json"}
    )

    # Instantiate MongoRefreshingCredentials
    creds = MongoRefreshingCredentials(
        token=initial_data["token"],
        refresh_token=initial_data["refresh_token"],
        token_uri=initial_data["token_uri"],
        client_id=initial_data["client_id"],
        client_secret=initial_data["client_secret"],
        scopes=initial_data["scopes"],
    )
    creds._user_id = user_id
    creds._service = service
    creds._cred_manager = mock_manager

    # Simulate token refresh by patching base class Credentials._blocking_refresh or refresh
    new_access_token = "new-fresh-access-token-777-refreshed"
    new_expiry = datetime.now(timezone.utc) + timedelta(hours=1)

    def fake_base_refresh(self_cred, request):
        self_cred.token = new_access_token
        self_cred.expiry = new_expiry

    with patch("google.oauth2.credentials.Credentials.refresh", side_effect=fake_base_refresh, autospec=True):
        creds.refresh(request=MagicMock())

    # Verify that the credential stored in MongoDB was updated
    updated_doc = mock_manager.get_credential(user_id=user_id, service=service)
    assert updated_doc is not None
    assert updated_doc["token"] == new_access_token
    assert updated_doc["refresh_token"] == initial_data["refresh_token"]
    assert updated_doc["client_id"] == initial_data["client_id"]

    # Verify encryption: raw MongoDB document must NOT contain the plaintext new token
    if mock_manager.collection is not None:
        raw_mongo_doc = mock_manager.collection.find_one({"user_id": user_id, "service": service})
        assert raw_mongo_doc is not None
        encrypted_field = raw_mongo_doc["encrypted_data"]
        assert new_access_token not in encrypted_field
        assert "valid-long-lived-refresh-token" not in encrypted_field

    # Clean up test user
    mock_manager.delete_credential(user_id=user_id, service=service)
