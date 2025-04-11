from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from typing import Optional, Dict, Any, Union
from beanie import PydanticObjectId
from enum import Enum

# --- Enums ---
class TaskStatus(str, Enum):
    PENDING = "PENDING"
    GATHERING_CONTEXT = "GATHERING_CONTEXT"
    PLANNING = "PLANNING"
    IMPLEMENTING = "IMPLEMENTING"
    TESTING = "TESTING"
    CREATING_BRANCH = "CREATING_BRANCH" # Added explicit branching state
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class InputSourceType(str, Enum):
    TEXT = "TEXT"
    TRELLO = "TRELLO"
    GOOGLE_DOC = "GOOGLE_DOC"
    # Add other types as needed

# --- Main Data Schema ---
class TaskData(BaseModel):
    """Data schema for representing task information."""
    id: PydanticObjectId = Field(..., alias="_id")
    chat_id: PydanticObjectId
    user_id: PydanticObjectId
    status: TaskStatus
    input_source_type: InputSourceType
    input_data: Union[str, HttpUrl, Dict[str, Any]]
    gathered_context: Optional[Dict[str, Any]] = None
    plan: Optional[Union[str, Dict[str, Any]]] = None
    results: Optional[Dict[str, Any]] = None
    error_details: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True, # Allow creating from model instances
        "populate_by_name": True, # Allow using '_id' alias
        "json_schema_extra": {
            "example": {
                "id": "65f1a7d8c3b4e9a1b7f8d3c1",
                "chat_id": "65f1a7d8c3b4e9a1b7f8d3c0",
                "user_id": "65f1a7d8c3b4e9a1b7f8d3bf",
                "status": "PENDING",
                "input_source_type": "TEXT",
                "input_data": "Fix the login button alignment on mobile",
                "gathered_context": None,
                "plan": None,
                "results": None,
                "error_details": None,
                "created_at": "2023-03-13T10:00:00Z",
                "updated_at": "2023-03-13T10:00:00Z",
            }
        }
    }

# We can add TaskCreate, TaskUpdate, GetTasksResponse later as needed. 