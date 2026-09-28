"""
Thread and Message Repository implementation using SQLAlchemy Session.
Adheres to SRP and enforces strict tenant/user boundary isolation.
"""
from typing import Optional, List
import uuid
from sqlalchemy.orm import Session
from nexusai.db.models import Thread, Message
from nexusai.repositories.base import IBaseRepository


class ThreadRepository(IBaseRepository[Thread]):
    """Data access repository for conversation Threads and Messages."""

    def __init__(self, db: Session):
        self._db = db

    def get_by_id(self, thread_id: str) -> Optional[Thread]:
        """Fetch thread strictly by ID."""
        return self._db.query(Thread).filter(Thread.id == str(thread_id)).first()

    def get_user_thread(self, thread_id: str, user_id: str) -> Optional[Thread]:
        """Fetch thread ensuring it strictly belongs to user_id (tenant isolation)."""
        return (
            self._db.query(Thread)
            .filter(Thread.id == str(thread_id), Thread.user_id == str(user_id))
            .first()
        )

    def list_by_user(self, user_id: str) -> List[Thread]:
        """Retrieve all threads belonging strictly to user_id in reverse chronological order."""
        return (
            self._db.query(Thread)
            .filter(Thread.user_id == str(user_id))
            .order_by(Thread.created_at.desc())
            .all()
        )

    def create(self, user_id: str, title: str = "New Chat", thread_id: Optional[str] = None) -> Thread:
        """Create a new thread scoped to user_id."""
        t_id = thread_id or str(uuid.uuid4())
        thread = Thread(id=t_id, user_id=str(user_id), title=title)
        self._db.add(thread)
        self._db.commit()
        self._db.refresh(thread)
        return thread

    def delete(self, thread: Thread) -> None:
        """Delete thread and cascade delete its messages."""
        self._db.delete(thread)
        self._db.commit()

    def add_message(self, thread_id: str, user_id: str, role: str, content: str) -> Message:
        """Persist a chat message within a thread."""
        msg = Message(
            thread_id=str(thread_id),
            user_id=str(user_id),
            role=role,
            content=content
        )
        self._db.add(msg)
        self._db.commit()
        self._db.refresh(msg)
        return msg

    def get_messages(self, thread_id: str) -> List[Message]:
        """Retrieve all messages for a thread in chronological order."""
        return (
            self._db.query(Message)
            .filter(Message.thread_id == str(thread_id))
            .order_by(Message.created_at.asc())
            .all()
        )
