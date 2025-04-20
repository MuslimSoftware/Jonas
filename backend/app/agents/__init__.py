# agents/__init__.py

# This file makes the 'agents' directory a Python package.

# Import agent instances and names
from .jonas_agent import jonas_agent, JONAS_NAME
from .browser_agent import browser_agent, BROWSER_AGENT_NAME
from .database_agent import database_agent, DATABASE_AGENT_NAME # Import DatabaseAgent

# Define the root agent for the application
# This is typically the main orchestrator or entry point agent.
root_agent = jonas_agent

# Optionally, define a dictionary for easy access by name
AGENTS = {
    JONAS_NAME: jonas_agent,
    BROWSER_AGENT_NAME: browser_agent,
    DATABASE_AGENT_NAME: database_agent # Add DatabaseAgent
}

# Export necessary components
__all__ = [
    "root_agent",
    "jonas_agent", 
    "browser_agent",
    "database_agent", 
    
    "JONAS_NAME",
    "BROWSER_AGENT_NAME",
    "DATABASE_AGENT_NAME", 
    "AGENTS"
]