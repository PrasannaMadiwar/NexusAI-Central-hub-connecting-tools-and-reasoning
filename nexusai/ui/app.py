"""
NexusAI Web UI Runner.
Launches the lightweight, scalable Web UI served directly by FastAPI.
Replaced legacy Streamlit frontend with zero-memory-leak, high-performance web interface.
"""
import sys
import webbrowser
from pathlib import Path

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).parent.parent.parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def run_ui(host: str = "127.0.0.1", port: int = 8000, reload: bool = True):
    """Launch the NexusAI web application."""
    import uvicorn
    print(f"Starting NexusAI Web UI on http://{host}:{port} ...")
    try:
        webbrowser.open(f"http://{host}:{port}")
    except Exception:
        pass
    uvicorn.run("nexusai.api.server:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    run_ui()
