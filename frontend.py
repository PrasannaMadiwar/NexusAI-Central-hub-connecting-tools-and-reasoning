"""
NexusAI Web Frontend Entrypoint.
Serves the ChatGPT / Gemini style HTML/CSS/JS frontend directly via FastAPI on http://127.0.0.1:8000
"""
import sys
import webbrowser
import uvicorn
from pathlib import Path

ROOT_DIR = Path(__file__).parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

if __name__ == "__main__":
    print("Starting NexusAI ChatGPT / Gemini Web Interface on http://127.0.0.1:8000 ...")
    try:
        webbrowser.open("http://127.0.0.1:8000")
    except Exception:
        pass
    uvicorn.run("nexusai.api.server:app", host="127.0.0.1", port=8000, reload=True)
