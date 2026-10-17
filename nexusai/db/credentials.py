import os
import json
import base64
import time
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from cryptography.fernet import Fernet
import certifi
import pymongo
from pymongo.collection import Collection

load_dotenv()


class CredentialsNotFoundError(Exception):
    """Raised when credentials for a specific user and service are not found."""
    pass


# Setup Encryption Key
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY") or os.getenv("ENCRYPTION_MASTER_KEY")
if not ENCRYPTION_KEY:
    default_secret = os.getenv("OPENAI_API_KEY") or os.getenv("GROQ_API_KEY", "nexusai-default-encryption-secret-key-32b")
    key_bytes = default_secret.encode()[:32].ljust(32, b"x")
    ENCRYPTION_KEY = base64.urlsafe_b64encode(key_bytes).decode()

fernet = Fernet(ENCRYPTION_KEY.encode())


try:
    from google.oauth2.credentials import Credentials as OAuthCredentials
except ImportError:
    OAuthCredentials = object


class MongoRefreshingCredentials(OAuthCredentials):
    """
    Subclass of google.oauth2.credentials.Credentials that intercepts refresh()
    and automatically persists the newly acquired access token (and expiration) back
    to MongoDB encrypted with Fernet.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user_id = None
        self._service = None
        self._cred_manager = None

    def refresh(self, request):
        super().refresh(request)
        if self._user_id and self._service and self._cred_manager:
            try:
                updated = {
                    "token": self.token,
                    "refresh_token": self.refresh_token,
                    "token_uri": self.token_uri,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scopes": self.scopes,
                }
                if self.expiry:
                    updated["expiry"] = self.expiry.strftime("%Y-%m-%dT%H:%M:%SZ")

                existing_doc = None
                if self._cred_manager.collection is not None:
                    existing_doc = self._cred_manager.collection.find_one({
                        "user_id": self._user_id,
                        "service": self._service
                    })

                auth_type = existing_doc.get("auth_type", "oauth_token") if existing_doc else "oauth_token"
                metadata = existing_doc.get("metadata", {}) if existing_doc else {}
                metadata["last_refreshed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

                self._cred_manager.save_credential(
                    user_id=self._user_id,
                    service=self._service,
                    auth_type=auth_type,
                    credential_data=updated,
                    metadata=metadata
                )
            except Exception as e:
                print(f"[MongoRefreshingCredentials] Warning: Failed to persist refreshed token ({e})")


class CredentialManager:
    """
    Multi-tenant credential store connected strictly to a MongoDB server cluster.
    Stores and decrypts user credentials with Fernet AES-256 encryption.
    Strict tenant isolation: ZERO fallback to local files or static credentials.
    """

    def __init__(self, mongo_uri: Optional[str] = None, db_name: Optional[str] = None):
        self.mongo_uri = (
            mongo_uri
            or os.getenv("MONGODB_ATLAS_URI")
            or os.getenv("MONGO_URI")
            or os.getenv("MONGODB_URI")
            or "mongodb://localhost:27017"
        )
        self.db_name = db_name or os.getenv("MONGO_DB_NAME", "nexusai")
        self._client = None
        self._db = None
        self._connected = False
        self._connect()

    def _connect(self):
        try:
            self._client = pymongo.MongoClient(
                self.mongo_uri,
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=10000,
                tlsCAFile=certifi.where()
            )
            self._client.admin.command('ping')
            self._db = self._client[self.db_name]
            self._db.user_credentials.create_index(
                [("user_id", pymongo.ASCENDING), ("service", pymongo.ASCENDING)], 
                unique=True
            )
            self._connected = True
        except Exception as e:
            self._connected = False
            print(f"[CredentialManager] Warning: MongoDB server connection failed ({e}). Check MONGO_URI in .env.")

    @property
    def collection(self) -> Optional[Collection]:
        if not self._connected:
            self._connect()
        return self._db.user_credentials if self._connected else None

    # ----------------------------------------------------------------------------------
    # Encryption Helpers
    # ----------------------------------------------------------------------------------
    @staticmethod
    def encrypt_data(data: Dict[str, Any]) -> str:
        serialized = json.dumps(data).encode("utf-8")
        return fernet.encrypt(serialized).decode("utf-8")

    @staticmethod
    def decrypt_data(token: str) -> Dict[str, Any]:
        decrypted = fernet.decrypt(token.encode("utf-8"))
        return json.loads(decrypted.decode("utf-8"))

    # ----------------------------------------------------------------------------------
    # Core CRUD Operations (Strict User Isolation)
    # ----------------------------------------------------------------------------------
    def save_credential(
        self,
        user_id: str,
        service: str,
        auth_type: str,
        credential_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store encrypted credentials for a specific OAuth2 user in MongoDB.
        """
        if not user_id:
            raise ValueError("user_id must be provided from an authenticated OAuth2 session.")

        if self.collection is None:
            raise RuntimeError("MongoDB server is not reachable. Verify MONGO_URI in .env.")

        encrypted_payload = self.encrypt_data(credential_data)
        meta = metadata or {}
        meta["updated_at"] = time.time()

        doc = {
            "user_id": user_id,
            "service": service,
            "auth_type": auth_type,
            "encrypted_data": encrypted_payload,
            "metadata": meta,
        }

        self.collection.update_one(
            {"user_id": user_id, "service": service},
            {"$set": doc},
            upsert=True
        )
        return True

    def get_credential(self, user_id: str, service: str) -> Optional[Dict[str, Any]]:
        """Retrieve and decrypt credentials strictly belonging to user_id."""
        if not user_id:
            return None

        if self.collection is None:
            raise CredentialsNotFoundError("MongoDB server is not connected. Please configure MONGO_URI in .env.")

        doc = self.collection.find_one({"user_id": user_id, "service": service})
        if not doc or "encrypted_data" not in doc:
            return None

        try:
            data = self.decrypt_data(doc["encrypted_data"])
            data["_auth_type"] = doc.get("auth_type")
            data["_metadata"] = doc.get("metadata", {})
            return data
        except Exception as e:
            print(f"[CredentialManager] Decryption error for user {user_id}, service {service}: {e}")
            return None

    def list_user_credentials(self, user_id: str) -> List[Dict[str, Any]]:
        """List active integrations strictly for user_id without exposing secrets."""
        if not user_id or self.collection is None:
            return []

        results = []
        for doc in self.collection.find({"user_id": user_id}):
            results.append({
                "service": doc.get("service"),
                "auth_type": doc.get("auth_type"),
                "metadata": doc.get("metadata", {}),
            })
        return results

    def delete_credential(self, user_id: str, service: str) -> bool:
        """Delete stored credential for a user and service."""
        if not user_id or self.collection is None:
            return False
        res = self.collection.delete_one({"user_id": user_id, "service": service})
        return res.deleted_count > 0

    # ----------------------------------------------------------------------------------
    # Dynamic Google & Zoom Service Builders (ZERO Local File Fallbacks)
    # ----------------------------------------------------------------------------------
    @staticmethod
    def _clean_cred_info(cred_info: Dict[str, Any]) -> tuple:
        """Strip internal _auth_type/_metadata keys and return (clean_data, auth_type).
        Google APIs will error on unknown keys, so we must remove our internal fields."""
        auth_type = cred_info.pop("_auth_type", None)
        cred_info.pop("_metadata", None)
        return cred_info, auth_type

    def get_calendar_service(self, user_id: str):
        """
        Builds a Google Calendar API service instance strictly from the user's MongoDB credentials.
        Original engine file: callender_api_agent_key.json (Service Account)
        """
        if not user_id:
            raise ValueError("user_id must be provided from an authenticated session.")

        try:
            from google.oauth2 import service_account
            from google.oauth2.credentials import Credentials as OAuthCredentials
            from googleapiclient.discovery import build
        except ImportError:
            raise ImportError("Google client libraries not found. Run: pip install google-api-python-client google-auth")

        scopes = ["https://www.googleapis.com/auth/calendar"]
        cred_info = self.get_credential(user_id, "google_calendar")
        if not cred_info:
            raise CredentialsNotFoundError(
                f"No Google Calendar credentials found for user '{user_id}'. "
                "Please upload your Calendar Service Account JSON "
                "(originally callender_api_agent_key.json) or OAuth token in Credentials Vault."
            )

        cred_info, auth_type = self._clean_cred_info(cred_info)
        if auth_type == "service_account":
            creds = service_account.Credentials.from_service_account_info(cred_info, scopes=scopes)
        else:
            creds = MongoRefreshingCredentials.from_authorized_user_info(cred_info, scopes=scopes)
            creds._user_id = user_id
            creds._service = "google_calendar"
            creds._cred_manager = self

        return build("calendar", "v3", credentials=creds)

    def get_gmail_service(self, user_id: str):
        """
        Builds a Gmail API service instance strictly from the user's MongoDB credentials.
        Original engine file: token.json (OAuth2 Token — NOT a Service Account)
        """
        if not user_id:
            raise ValueError("user_id must be provided from an authenticated session.")

        try:
            from google.oauth2.credentials import Credentials as OAuthCredentials
            from googleapiclient.discovery import build
        except ImportError:
            raise ImportError("Google client libraries not found. Run: pip install google-api-python-client google-auth")

        scopes = [
            "https://mail.google.com/",
            "https://www.googleapis.com/auth/gmail.modify",
            "https://www.googleapis.com/auth/gmail.compose",
            "https://www.googleapis.com/auth/gmail.readonly",
        ]

        cred_info = self.get_credential(user_id, "gmail")
        if not cred_info:
            raise CredentialsNotFoundError(
                f"No Gmail credentials found for user '{user_id}'. "
                "Please upload your Gmail OAuth2 token.json file in Credentials Vault. "
                "Note: Gmail requires an OAuth2 token (token.json), NOT a Service Account JSON."
            )

        cred_info, auth_type = self._clean_cred_info(cred_info)

        # Gmail API only supports OAuth2 user tokens, NOT service accounts.
        # If user uploaded a service account JSON for Gmail, reject with clear error.
        if auth_type == "service_account":
            raise CredentialsNotFoundError(
                f"Gmail for user '{user_id}' has a Service Account JSON stored, but Gmail "
                "requires an OAuth2 token (token.json). Please remove the current credential "
                "and upload your token.json instead."
            )

        # Use granted scopes from token.json or default to full Gmail access
        token_scopes = cred_info.get("scopes") or ["https://mail.google.com/"]
        creds = MongoRefreshingCredentials.from_authorized_user_info(cred_info, scopes=token_scopes)
        creds._user_id = user_id
        creds._service = "gmail"
        creds._cred_manager = self
        return build("gmail", "v1", credentials=creds)

    def get_drive_and_docs_services(self, user_id: str):
        """
        Builds Google Drive and Docs API service instances strictly from the user's MongoDB credentials.
        Used by: Google Meet transcript tools (list_google_meet_transcripts, get_google_meet_transcript)
        Original engine: Service Account JSON with Drive/Docs readonly scopes
        """
        if not user_id:
            raise ValueError("user_id must be provided from an authenticated session.")

        try:
            from google.oauth2 import service_account
            from google.oauth2.credentials import Credentials as OAuthCredentials
            from googleapiclient.discovery import build
        except ImportError:
            raise ImportError("Google client libraries not found. Run: pip install google-api-python-client google-auth")

        scopes = [
            "https://www.googleapis.com/auth/drive.readonly",
            "https://www.googleapis.com/auth/documents.readonly"
        ]

        cred_info = self.get_credential(user_id, "google_meet")
        if not cred_info:
            raise CredentialsNotFoundError(
                f"No Google Meet/Drive credentials found for user '{user_id}'. "
                "Please upload your Google Drive/Meet Service Account JSON "
                "or OAuth token in Credentials Vault."
            )

        cred_info, auth_type = self._clean_cred_info(cred_info)
        if auth_type == "service_account":
            creds = service_account.Credentials.from_service_account_info(cred_info, scopes=scopes)
        else:
            creds = MongoRefreshingCredentials.from_authorized_user_info(cred_info, scopes=scopes)
            creds._user_id = user_id
            creds._service = "google_meet"
            creds._cred_manager = self

        return build("drive", "v3", credentials=creds), build("docs", "v1", credentials=creds)

    def get_zoom_access_token(self, user_id: str) -> str:
        """
        Fetches a Zoom OAuth access token strictly using the user's credentials in MongoDB.
        Original engine: ZOOM_ACCOUNT_ID, ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET from .env
        Now stored in MongoDB under service key 'zoom'.
        """
        import requests

        if not user_id:
            raise ValueError("user_id must be provided from an authenticated session.")

        cred_info = self.get_credential(user_id, "zoom")
        if not cred_info:
            raise CredentialsNotFoundError(
                f"No Zoom credentials found for user '{user_id}'. "
                "Please enter your Zoom Server-to-Server OAuth credentials "
                "(Account ID, Client ID, Client Secret) in the Credentials Vault → Zoom S2S tab."
            )

        # Strip internal keys
        cred_info.pop("_auth_type", None)
        cred_info.pop("_metadata", None)

        account_id = cred_info.get("account_id")
        client_id = cred_info.get("client_id")
        client_secret = cred_info.get("client_secret")

        if not account_id or not client_id or not client_secret:
            raise ValueError(
                "Incomplete Zoom credentials. Required fields: account_id, client_id, client_secret. "
                "Please re-enter your Zoom S2S credentials in Credentials Vault."
            )

        auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        token_url = f"https://zoom.us/oauth/token?grant_type=account_credentials&account_id={account_id}"

        response = requests.post(
            token_url,
            headers={
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            timeout=10
        )

        if response.status_code != 200:
            raise RuntimeError(f"Zoom OAuth token request failed: {response.text}")

        return response.json().get("access_token")


# Global singleton instance
credential_manager = CredentialManager()
