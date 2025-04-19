# agents/jonas_agent/__init__.py

from .agent import jonas_agent
from .agent import JONAS_NAME

# Export only the specific agent instance and name
__all__ = ["jonas_agent", "JONAS_NAME"] 