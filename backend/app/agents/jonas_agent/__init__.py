# agents/jonas_agent/__init__.py

from .agent import jonas_agent

# Optional alias if ADK tools look for 'root_agent' by convention
root_agent = jonas_agent

__all__ = ["jonas_agent", "root_agent"] 