# agents/__init__.py

# This file makes the 'agents' directory a Python package.

# Export only the primary agent
from .jonas_agent import jonas_agent
# No need to explicitly import/export browser_agent here if Jonas imports it
# from .browser_agent import browser_agent 

# Export only the primary entry point agent
__all__ = [
    "root_agent",
    "jonas_agent"
]