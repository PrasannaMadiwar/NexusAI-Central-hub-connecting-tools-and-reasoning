"""
Chat Service.
Coordinates LangGraph orchestrator invocation, thread creation, and message persistence.
Adheres to SRP by decoupling chat orchestration from HTTP routing.
"""
from typing import Dict, Any, Optional
import uuid
from langchain_core.messages import HumanMessage, AIMessage

from nexusai.repositories.thread_repository import ThreadRepository
from nexusai.engine.orchestrator import agent
from nexusai.db.models import User, Thread


class ChatService:
    """Service layer managing agent conversations and chat history."""

    def __init__(self, thread_repo: ThreadRepository):
        self._thread_repo = thread_repo

    def process_chat(self, user: User, message: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process chat message with agent orchestrator and store history.
        Ensures thread ownership and user isolation.
        """
        active_thread_id = thread_id or str(uuid.uuid4())

        # Retrieve or create thread
        thread = self._thread_repo.get_user_thread(active_thread_id, user.id)
        if not thread:
            snippet = message[:40] + ("..." if len(message) > 40 else "")
            thread = self._thread_repo.create(user_id=user.id, title=snippet, thread_id=active_thread_id)

        # Save user message
        self._thread_repo.add_message(
            thread_id=active_thread_id,
            user_id=user.id,
            role="user",
            content=message
        )

        # Configure LangGraph context
        config = {
            "configurable": {
                "thread_id": active_thread_id,
                "user_id": user.id,
            },
            "metadata": {
                "thread_id": active_thread_id,
                "user_id": user.id,
            }
        }

        try:
            response = agent.invoke({"messages": [HumanMessage(message)]}, config=config)
            messages = response.get("messages", [])
            ai_text = "I have processed your request."
            for m in reversed(messages):
                if isinstance(m, AIMessage) and not getattr(m, "tool_calls", None) and m.content:
                    ai_text = str(m.content)
                    break

            # Persist assistant response
            self._thread_repo.add_message(
                thread_id=active_thread_id,
                user_id=user.id,
                role="assistant",
                content=ai_text
            )

            return {
                "thread_id": active_thread_id,
                "response": ai_text
            }
        except Exception as e:
            error_msg = f"Agent execution error: {str(e)}"
            self._thread_repo.add_message(
                thread_id=active_thread_id,
                user_id=user.id,
                role="assistant",
                content=f"Error: {error_msg}"
            )
            return {
                "thread_id": active_thread_id,
                "response": f"Error: {error_msg}"
            }
