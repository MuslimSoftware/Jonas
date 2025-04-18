# agents/browser_agent/__init__.py

from .agent import browser_agent
from .tools import run_browser_task_tool # Keep tool export if needed elsewhere?

# Export the agent and potentially the tool if it might be used independently
__all__ = ["browser_agent", "run_browser_task_tool"]

# This file makes the directory a Python package 