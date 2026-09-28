"""
User Repository implementation using SQLAlchemy Session.
Adheres to Single Responsibility Principle (SRP) for user data access.
"""
from typing import Optional
from sqlalchemy.orm import Session
from nexusai.db.models import User
from nexusai.repositories.base import IBaseRepository


class UserRepository(IBaseRepository[User]):
    """Data access repository for User entities."""

    def __init__(self, db: Session):
        self._db = db

    def get_by_id(self, user_id: str) -> Optional[User]:
        """Fetch user by primary ID."""
        return self._db.query(User).filter(User.id == str(user_id)).first()

    def get_by_email(self, email: str) -> Optional[User]:
        """Fetch user by normalized lowercase email."""
        return self._db.query(User).filter(User.email == email.strip().lower()).first()

    def create(self, user_id: str, email: str, password_hash: Optional[str] = None) -> User:
        """Create and persist a new user record."""
        user = User(
            id=str(user_id),
            email=email.strip().lower(),
            password_hash=password_hash
        )
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user

    def sync_oauth_user(self, user_id: str, email: Optional[str] = None) -> User:
        """Ensure an authenticated OAuth2 / JWT user exists in the local database."""
        user = self.get_by_id(user_id)
        if not user:
            user = User(
                id=str(user_id),
                email=email or f"{user_id}@oauth.user"
            )
            self._db.add(user)
            self._db.commit()
            self._db.refresh(user)
        return user
