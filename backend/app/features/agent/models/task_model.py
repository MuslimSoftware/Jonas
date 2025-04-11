from beanie import Document, PydanticObjectId
from pydantic import Field, HttpUrl
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Union

from ..schemas.task_schemas import TaskStatus, InputSourceType # Relative import

class Task(Document):
    """Model representing an automated task for the Jonas agent."""

    # Core Identifiers
    chat_id: PydanticObjectId
    user_id: PydanticObjectId # User who initiated the task

    # Status & Workflow
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    input_source_type: InputSourceType
    input_data: Union[str, HttpUrl, Dict[str, Any]] # Store URL, ID, or raw text/data

    # Stored Data from Phases
    gathered_context: Optional[Dict[str, Any]] = Field(default=None)
    plan: Optional[Union[str, Dict[str, Any]]] = Field(default=None) # Could be text or structured plan
    results: Optional[Dict[str, Any]] = Field(default=None) # e.g., {"test_output": "...", "branch_name": "..."}
    error_details: Optional[str] = Field(default=None) # Store error message if status is FAILED

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "agent_tasks"
        indexes = [
            [("user_id", 1), ("created_at", -1)],
            [("chat_id", 1)],
            [("status", 1)],
        ]

    # Need to manually trigger updated_at on saves usually,
    # Beanie doesn't automatically update it like some other ORMs.
    # We'll handle this in the repository/service layer. 