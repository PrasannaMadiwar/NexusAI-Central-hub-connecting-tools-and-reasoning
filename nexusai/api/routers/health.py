"""
Health Check Router.
Provides comprehensive system diagnostics, live DB connection status,
MongoDB vault availability, and Redis check (if used).
"""
import os
from datetime import datetime, timezone
from fastapi import APIRouter
from sqlalchemy import text
from nexusai.db.models import engine
from nexusai.db.credentials import credential_manager

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    """
    Comprehensive system health check endpoint:
    - Tests relational DB connectivity (PostgreSQL/SQLite)
    - Tests MongoDB vault cluster ping
    - Reports Redis status (not configured / not used)
    """
    # 1. Relational Database Check
    db_status = "unhealthy"
    db_type = "PostgreSQL" if "postgres" in str(engine.url).lower() else "SQLite"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    # 2. MongoDB Cluster Vault Check
    mongo_status = "unhealthy"
    try:
        if credential_manager._client is not None:
            credential_manager._client.admin.command("ping")
            mongo_status = "connected"
        elif credential_manager.collection is not None:
            mongo_status = "connected"
        else:
            mongo_status = "offline"
    except Exception as e:
        mongo_status = f"error: {str(e)}"

    # 3. Redis Check (Architecture uses PostgresSaver / MemorySaver + Mongo Vault)
    redis_used = bool(os.getenv("REDIS_URL"))
    redis_status = "not_used" if not redis_used else "configured"

    is_healthy = (db_status == "connected") and (mongo_status == "connected")
    overall_status = "healthy" if is_healthy else "degraded"

    return {
        "status": overall_status,
        "checks": {
            "database": {
                "status": db_status,
                "type": db_type,
            },
            "mongodb": {
                "status": mongo_status,
            },
            "redis": {
                "status": redis_status,
                "used": redis_used,
            }
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2.0.0"
    }
