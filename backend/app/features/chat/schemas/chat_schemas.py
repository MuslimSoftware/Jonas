from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Literal
from beanie import PydanticObjectId

from app.features.common.schemas import BaseResponse 

# --- Core Data Models --- 

class MessageData(BaseModel):
    """Core data representation for a message."""
    id: PydanticObjectId = Field(..., alias="_id") # Map from MongoDB's _id
    sender_type: Literal['user', 'agent'] = 'user'
    content: str
    author_id: Optional[PydanticObjectId] = None
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True # Allow using alias `_id` for `id`
        json_schema_extra = {
            "example": {
                "id": "60d5ec49abf8a7b6a0f3e8f1",
                "sender_type": "user",
                "content": "Hello there!",
                "author_id": "60d5ec49abf8a7b6a0f3e8f1",
                "created_at": "2023-01-01T12:00:00Z",
            }
        }

class ChatData(BaseModel):
    """Core data representation for a chat, including messages for detail view."""
    id: PydanticObjectId = Field(..., alias="_id") # Map from MongoDB's _id
    name: Optional[str] = None
    owner_id: PydanticObjectId
    created_at: datetime
    updated_at: datetime
    messages: List[MessageData] = []

    class Config:
        from_attributes = True
        populate_by_name = True # Allow using alias `_id` for `id`
        json_schema_extra = {
            "example": {
                "id": "60d5ec49abf8a7b6a0f3e8f2",
                "name": "User's Chat",
                "owner_id": "60d5ec49abf8a7b6a0f3e8f1",
                "created_at": "2023-01-01T12:00:00Z",
                "updated_at": "2023-01-01T12:00:00Z",
                "messages": [] # Example messages could be added here
            }
        }

# --- Request Payloads (Inputs) --- 

class MessageCreate(BaseModel):
    sender_type: Literal['user', 'agent'] = 'user'
    content: str

class ChatCreate(BaseModel):
    name: Optional[str] = None

# --- API Response Schemas (Outputs using BaseResponse) --- 

class GetChatsResponse(BaseResponse[List[ChatData]]):
    """Response schema for listing chats (contains basic chat info, no messages)."""
    # Note: We use ChatData here, but the controller logic should ensure
    # the repository doesn't fetch messages for this endpoint.
    # FastAPI will serialize based on this schema, effectively omitting messages.
    pass

class GetChatDetailsResponse(BaseResponse[ChatData]):
    """Response schema for getting detailed chat information, including messages."""
    pass

class CreateChatResponse(BaseResponse[ChatData]):
    """Response schema after creating a new chat."""
    pass

class AddMessageResponse(BaseResponse[MessageData]):
    """Response schema after adding a new message."""
    pass
