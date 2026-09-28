"""
Conversation Threads and Messages Router.
Enforces strict tenant isolation across conversation threads.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from nexusai.api.schemas import ThreadCreateRequest
from nexusai.repositories.thread_repository import ThreadRepository
from nexusai.api.dependencies import get_thread_repository, get_current_user
from nexusai.db.models import User

router = APIRouter(prefix="/api/threads", tags=["Threads"])


@router.get("")
def list_threads(user: User = Depends(get_current_user), thread_repo: ThreadRepository = Depends(get_thread_repository)):
    """Retrieve all threads strictly belonging to the authenticated user."""
    threads = thread_repo.list_by_user(user.id)
    return [
        {
            "id": t.id,
            "title": t.title,
            "created_at": t.created_at.isoformat() if t.created_at else None
        }
        for t in threads
    ]


@router.post("")
def create_thread(
    req: ThreadCreateRequest,
    user: User = Depends(get_current_user),
    thread_repo: ThreadRepository = Depends(get_thread_repository)
):
    """Create a new conversation thread for the authenticated user."""
    thread = thread_repo.create(user_id=user.id, title=req.title or "New Chat")
    return {"id": thread.id, "title": thread.title, "user_id": thread.user_id}


@router.get("/{thread_id}/messages")
def get_thread_messages(
    thread_id: str,
    user: User = Depends(get_current_user),
    thread_repo: ThreadRepository = Depends(get_thread_repository)
):
    """Get message history for a specific thread, verifying user ownership."""
    thread = thread_repo.get_user_thread(thread_id, user.id)
    if not thread:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found or access denied.")

    messages = thread_repo.get_messages(thread_id)
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat() if m.created_at else None
        }
        for m in messages
    ]


@router.delete("/{thread_id}")
def delete_thread(
    thread_id: str,
    user: User = Depends(get_current_user),
    thread_repo: ThreadRepository = Depends(get_thread_repository)
):
    """Delete a thread and its messages belonging to the authenticated user."""
    thread = thread_repo.get_user_thread(thread_id, user.id)
    if not thread:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found or access denied.")

    thread_repo.delete(thread)
    return {"status": "deleted", "thread_id": thread_id}
