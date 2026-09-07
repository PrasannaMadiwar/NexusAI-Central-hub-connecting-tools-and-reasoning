"""
Root entrypoint for NexusAI Streamlit Workspace UI.
Proxies to modular package: nexusai/ui/app.py
"""
import sys
import runpy
from pathlib import Path

ROOT_DIR = Path(__file__).parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Execute modular Streamlit application
APP_PATH = ROOT_DIR / "nexusai" / "ui" / "app.py"
runpy.run_path(str(APP_PATH), run_name="__main__")
