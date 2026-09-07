"""
Root entrypoint for NexusAI DeepAgent Orchestrator.
Proxies to modular package: nexusai.engine.orchestrator
"""
import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from nexusai.engine.orchestrator import *
