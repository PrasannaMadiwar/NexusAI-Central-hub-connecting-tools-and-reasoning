"""
Database package for NexusAI: PostgreSQL SQLAlchemy models and MongoDB credentials vault.
"""
from nexusai.db.models import (
    Base,
    engine,
    SessionLocal,
    User,
    Thread,
    Message,
    init_db,
    get_db,
)
from nexusai.db.credentials import (
    CredentialManager,
    credential_manager,
    CredentialsNotFoundError,
)

__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "User",
    "Thread",
    "Message",
    "init_db",
    "get_db",
    "CredentialManager",
    "credential_manager",
    "CredentialsNotFoundError",
]
