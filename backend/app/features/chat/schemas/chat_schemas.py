from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Literal
from beanie import PydanticObjectId

class MessageBase(BaseModel):
    sender_type: Literal['user', 'agent'] = 'user'
    content: str

class MessageCreate(MessageBase):
    pass

class MessageRead(MessageBase):
    id: PydanticObjectId
    author_id: Optional[PydanticObjectId] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ChatBase(BaseModel):
    name: Optional[str] = None

class ChatCreate(ChatBase):
    pass

class ChatRead(ChatBase):
    id: PydanticObjectId
    owner_id: PydanticObjectId
    created_at: datetime
    updated_at: datetime
    messages: List[MessageRead] = []

    class Config:
        from_attributes = True

class ChatReadBasic(ChatBase):
    id: PydanticObjectId
    owner_id: PydanticObjectId
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 