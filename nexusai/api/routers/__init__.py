"""
NexusAI API Routers Package.
"""
from nexusai.api.routers.health import router as health_router
from nexusai.api.routers.auth import router as auth_router
from nexusai.api.routers.threads import router as threads_router
from nexusai.api.routers.chat import router as chat_router
from nexusai.api.routers.credentials import router as credentials_router

__all__ = [
    "health_router",
    "auth_router",
    "threads_router",
    "chat_router",
    "credentials_router",
]
