from enum import Enum
from typing import Optional
from pydantic import BaseModel
from beanie import PydanticObjectId

class AgentOutputType(str, Enum):
    """Defines the types of output events the AgentService recognizes."""
    STREAM_START = "stream_start"    # First chunk of a streamed response (includes message_id)
    STREAM_CHUNK = "stream_chunk"    # Subsequent chunk of a streamed response
    STREAM_END = "stream_end"        # Indicates the end of a streamed response
    FINAL_MESSAGE = "final_message" # A complete, non-streamed message
    DELEGATION = "delegation"        # Agent is delegating to another agent
    TOOL_RESULT = "tool_result"      # The result returned by a tool call
    ERROR = "error"                  # An error occurred during processing
    # Add other types as needed (e.g., TOOL_CALL)

class AgentOutputEvent(BaseModel):
    """Structured data yielded by ADKService (internal to Agent feature)."""
    type: AgentOutputType
    content: Optional[str] = None
    message_id: Optional[PydanticObjectId] = None # ID of the corresponding message in DB
    tool_name: Optional[str] = None # e.g., agent name for delegation, tool name for tool events
    # Add other relevant fields like error codes, metadata etc.

    class Config:
        arbitrary_types_allowed = True # Allow PydanticObjectId 

class ToolResult(BaseModel):
    """Structured data yielded by ADKService (internal to Agent feature)."""
    result: str