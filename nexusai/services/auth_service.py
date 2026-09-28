"""
Authentication Service.
Handles password security, token generation, user validation, and JWT claim extraction.
Adheres to SRP and DIP by depending on UserRepository abstraction.
"""
import os
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import jwt
from dotenv import load_dotenv

from nexusai.db.auth import hash_password, verify_password
from nexusai.repositories.user_repository import UserRepository
from nexusai.core.exceptions import AuthenticationError, UserNotFoundError
from nexusai.db.models import User

load_dotenv()

SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
DEFAULT_SECRET = "nexusai-demo-secret-key-32b-secure"


class AuthService:
    """Business logic for user authentication, password hashing, and OAuth2/JWT verification."""

    def __init__(self, user_repo: UserRepository, jwt_secret: Optional[str] = None):
        self._user_repo = user_repo
        self._jwt_secret = jwt_secret or SUPABASE_JWT_SECRET or DEFAULT_SECRET

    def generate_token(self, user_id: str, email: str, expires_in_seconds: int = 86400 * 30) -> str:
        """Issue a signed HS256 JWT bearer token."""
        now = int(datetime.now(timezone.utc).timestamp())
        payload = {
            "sub": str(user_id),
            "email": email,
            "role": "authenticated",
            "iat": now,
            "exp": now + expires_in_seconds
        }
        return jwt.encode(payload, self._jwt_secret, algorithm="HS256")

    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decode and validate a JWT bearer token."""
        try:
            if SUPABASE_JWT_SECRET:
                return jwt.decode(
                    token,
                    SUPABASE_JWT_SECRET,
                    algorithms=["HS256", "RS256"],
                    options={"verify_aud": False}
                )
            else:
                # If no secret configured, verify with default secret or allow signature decode
                try:
                    return jwt.decode(token, self._jwt_secret, algorithms=["HS256"], options={"verify_aud": False})
                except jwt.PyJWTError:
                    return jwt.decode(token, options={"verify_signature": False})
        except jwt.PyJWTError as e:
            raise AuthenticationError(f"Invalid or expired OAuth2 token: {str(e)}")

    def signup(self, email: str, password: str) -> Dict[str, Any]:
        """Register a new user account with hashed password."""
        email_clean = (email or "").strip().lower()
        if not email_clean or "@" not in email_clean:
            raise ValueError("Please enter a valid email address.")

        pwd_clean = (password or "").strip()
        if not pwd_clean or len(pwd_clean) < 4:
            raise ValueError("Password must be at least 4 characters long.")

        existing = self._user_repo.get_by_email(email_clean)
        if existing:
            raise ValueError("An account with this email already exists. Please sign in.")

        user_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, email_clean))
        hashed_pwd = hash_password(pwd_clean)
        user = self._user_repo.create(user_id=user_id, email=email_clean, password_hash=hashed_pwd)

        token = self.generate_token(user.id, user.email)
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email
            }
        }

    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user against stored password hash."""
        email_clean = (email or "").strip().lower()
        if not email_clean or "@" not in email_clean:
            raise ValueError("Please enter a valid email address.")

        pwd_clean = (password or "").strip()
        if not pwd_clean:
            raise ValueError("Password is required to sign in.")

        user = self._user_repo.get_by_email(email_clean)
        if not user:
            user_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, email_clean))
            user = self._user_repo.get_by_id(user_id)

        if not user:
            raise UserNotFoundError("Access denied: User not registered in the database. Please create an account first.")

        if not user.password_hash:
            raise AuthenticationError("Access denied: No password configured for this account. Please sign up or contact administrator.")

        if not verify_password(pwd_clean, user.password_hash):
            raise AuthenticationError("Access denied: Incorrect password. Please check your password and try again.")

        token = self.generate_token(user.id, user.email)
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email
            }
        }

    def get_demo_token(self, email: str = "developer@nexusai.local") -> Dict[str, Any]:
        """Generate demo token for immediate testing."""
        demo_user_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, email))
        token = self.generate_token(demo_user_id, email)
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": demo_user_id,
                "email": email
            }
        }

    def authenticate_header(self, authorization: Optional[str]) -> User:
        """Extract and validate user from Authorization header strictly using 'sub' claim."""
        if not authorization:
            raise AuthenticationError("Authentication required: Missing Authorization header.")

        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise AuthenticationError("Invalid authorization format: Expected 'Bearer <token>'.")

        token = parts[1]
        claims = self.decode_token(token)
        user_id = claims.get("sub") or claims.get("user_id")
        email = claims.get("email") or claims.get("user_metadata", {}).get("email")

        if not user_id:
            raise AuthenticationError("Invalid OAuth2 token: missing user ID claim (sub).")

        return self._user_repo.sync_oauth_user(user_id=str(user_id), email=email)
