"""
Credential Service.
Encapsulates all credential management operations using CredentialManager.
Adheres to SRP and shields API routes from low-level vault encryption / MongoDB logic.
"""
from typing import Dict, Any, List, Optional
import json
from nexusai.db.credentials import CredentialManager, credential_manager
from nexusai.core.exceptions import CredentialVaultError


class CredentialService:
    """Business logic service for managing encrypted multi-tenant credentials."""

    def __init__(self, manager: Optional[CredentialManager] = None):
        self._manager = manager or credential_manager

    def list_credentials(self, user_id: str) -> List[Dict[str, Any]]:
        """List active integrations for a user."""
        return self._manager.list_user_credentials(user_id=user_id)

    def save_zoom_credentials(self, user_id: str, account_id: str, client_id: str, client_secret: str) -> Dict[str, Any]:
        """Save encrypted Zoom Server-to-Server OAuth credentials."""
        data = {
            "account_id": account_id,
            "client_id": client_id,
            "client_secret": client_secret
        }
        self._manager.save_credential(
            user_id=user_id,
            service="zoom",
            auth_type="zoom_s2s",
            credential_data=data
        )
        return {
            "status": "success",
            "service": "zoom",
            "message": "Zoom credentials encrypted & saved in MongoDB."
        }

    def save_json_credential(self, user_id: str, service: str, file_content: bytes, filename: Optional[str] = None) -> Dict[str, Any]:
        """Parse and store encrypted Google Service Account or OAuth JSON."""
        try:
            data = json.loads(file_content.decode("utf-8"))
        except Exception as e:
            raise CredentialVaultError(f"Invalid JSON file: {e}")

        auth_type = "service_account" if data.get("type") == "service_account" else "oauth_token"
        self._manager.save_credential(
            user_id=user_id,
            service=service,
            auth_type=auth_type,
            credential_data=data,
            metadata={"filename": filename or "credentials.json"}
        )
        return {
            "status": "success",
            "service": service,
            "message": f"{service} credentials encrypted & saved in MongoDB."
        }

    def delete_credential(self, user_id: str, service: str) -> bool:
        """Remove a credential from the vault."""
        return self._manager.delete_credential(user_id=user_id, service=service)
