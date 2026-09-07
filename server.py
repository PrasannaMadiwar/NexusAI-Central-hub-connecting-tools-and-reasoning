"""
Root entrypoint for NexusAI FastAPI Server.
Proxies to modular package: nexusai.api.server
"""
import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from nexusai.api.server import app, get_current_user
from nexusai.api.schemas import ChatRequest, ThreadCreateRequest, ZoomCredentialRequest

__all__ = ["app", "get_current_user", "ChatRequest", "ThreadCreateRequest", "ZoomCredentialRequest"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("nexusai.api.server:app", host="127.0.0.1", port=8000, reload=True)
