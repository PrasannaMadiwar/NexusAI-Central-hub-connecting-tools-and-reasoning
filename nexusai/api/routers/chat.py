"""
Chat Orchestration Router.
Invokes the LangGraph DeepAgent orchestrator with authenticated user context.
"""
from fastapi import APIRouter, Depends
from nexusai.api.schemas import ChatRequest
from nexusai.services.chat_service import ChatService
from nexusai.api.dependencies import get_chat_service, get_current_user
from nexusai.db.models import User

router = APIRouter(tags=["Chat"])


@router.post("/api/chat")
def chat_with_nexus(
    req: ChatRequest,
    user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Execute NexusAI orchestrator with dynamic user context and store messages in database.
    """
    return chat_service.process_chat(
        user=user,
        message=req.message,
        thread_id=req.thread_id
    )
