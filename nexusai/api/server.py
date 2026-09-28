"""
NexusAI FastAPI Server Entrypoint & Application Factory.
Follows Low-Level Design (LLD) principles:
- Composition root wiring Routers, Middleware, and Static Web UI
- Re-exports get_current_user for backward compatibility
- Clean separation of concerns across Repositories, Services, and Controllers
"""
import os
from pathlib import Path
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from nexusai.db.models import init_db
from nexusai.api.dependencies import get_current_user
from nexusai.api.routers import (
    health_router,
    auth_router,
    threads_router,
    chat_router,
    credentials_router,
)

load_dotenv()

# Initialize tables on startup
init_db()


def create_application() -> FastAPI:
    """Factory creating and configuring the NexusAI FastAPI application."""
    application = FastAPI(
        title="NexusAI Central Hub API",
        description="Scalable multi-tenant AI workspace API with Supabase PostgreSQL (SQLAlchemy), MongoDB Credential Vault, and OAuth2 User Isolation.",
        version="2.0.0"
    )

    # Enable CORS for frontend clients
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register Domain Routers
    application.include_router(health_router)
    application.include_router(auth_router)
    application.include_router(threads_router)
    application.include_router(chat_router)
    application.include_router(credentials_router)

    # Mount Lightweight Web UI (Vanilla HTML/CSS/JS)
    web_dir = Path(__file__).parent.parent / "ui" / "web"
    if web_dir.exists():
        application.mount("/static", StaticFiles(directory=str(web_dir)), name="static")

        @application.get("/", include_in_schema=False)
        async def serve_index():
            response = FileResponse(str(web_dir / "index.html"))
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response

    return application


app = create_application()

__all__ = ["app", "get_current_user", "init_db", "create_application"]
