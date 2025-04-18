# agents/__init__.py

# This file makes the 'agents' directory a Python package.
# You can optionally export specific agents or modules from here if needed.

# Example: If you wanted to easily import jonas_agent directly from app.agents
# from .jonas_agent import jonas_agent, root_agent
# __all__ = ["jonas_agent", "root_agent"]

# Export the main agent(s) of the application
from .jonas_agent import jonas_agent
from .browser_agent import browser_agent # Export sub-agent too?

# Typically export the primary entry point agent
__all__ = ["jonas_agent", "browser_agent"] 