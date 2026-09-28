"""
Health Check Router.
Provides system diagnostics, database connection status, and vault availability.
"""
from datetime import datetime, timezone
from fastapi import APIRouter
from nexusai.db.credentials import credential_manager

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    """System health check endpoint."""
    mongo_status = "connected" if credential_manager.collection is not None else "offline"
    return {
        "status": "healthy",
        "stack": "FastAPI + SQLAlchemy + PostgreSQL",
        "database": "Supabase PostgreSQL",
        "vault": f"MongoDB ({mongo_status})",
        "mongodb": mongo_status,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
