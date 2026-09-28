"""
FastAPI Dependency Injection Providers.
Adheres to Dependency Inversion Principle (DIP).
Provides clean decoupling between HTTP controllers and underlying services/repositories.
"""
from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from nexusai.db.models import get_db, User
from nexusai.repositories.user_repository import UserRepository
from nexusai.repositories.thread_repository import ThreadRepository
from nexusai.services.auth_service import AuthService
from nexusai.services.chat_service import ChatService
from nexusai.services.credential_service import CredentialService
from nexusai.core.exceptions import AuthenticationError


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Dependency provider for UserRepository."""
    return UserRepository(db)


def get_thread_repository(db: Session = Depends(get_db)) -> ThreadRepository:
    """Dependency provider for ThreadRepository."""
    return ThreadRepository(db)


def get_auth_service(user_repo: UserRepository = Depends(get_user_repository)) -> AuthService:
    """Dependency provider for AuthService."""
    return AuthService(user_repo)


def get_chat_service(thread_repo: ThreadRepository = Depends(get_thread_repository)) -> ChatService:
    """Dependency provider for ChatService."""
    return ChatService(thread_repo)


def get_credential_service() -> CredentialService:
    """Dependency provider for CredentialService."""
    return CredentialService()


def get_current_user(
    authorization: Optional[str] = Header(None),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """
    Extracts and validates OAuth2 / Supabase user strictly from Authorization header JWT.
    Derives user_id STRICTLY from the verified token 'sub' claim.
    """
    try:
        return auth_service.authenticate_header(authorization)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
