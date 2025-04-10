from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, WebSocketException, Query
from beanie import PydanticObjectId
from pydantic import ValidationError
from datetime import datetime
from typing import Optional

from ..schemas import (
    ChatCreate, 
    MessageCreate, 
    GetChatsResponse, 
    GetChatDetailsResponse, 
    CreateChatResponse, 
    AddMessageResponse,
    GetChatMessagesResponse,
    ChatUpdate
)
from app.config.dependencies import ChatServiceDep, UserDep, ConnectionRepositoryDep, CurrentUserWsDep
from ..schemas import ChatData, MessageData
from ..managers.chat_websocket_manager import ChatWebSocketManager

router = APIRouter(
    prefix="/chats",
    tags=["Chat"]
)

# --- WebSocket Endpoint --- #

@router.websocket("/ws/{chat_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    chat_id: str,
    connection_repo: ConnectionRepositoryDep,
    current_user: CurrentUserWsDep,
    chat_service: ChatServiceDep
):
    try:
        chat_id_obj = PydanticObjectId(chat_id)
    except Exception:
        await websocket.close(code=status.WS_1007_INVALID_FRAMEWORK_PAYLOAD_DATA, reason="Invalid chat ID format")
        return

    manager = ChatWebSocketManager(
        websocket=websocket,
        chat_id=chat_id_obj,
        user=current_user,
        chat_service=chat_service,
        connection_repo=connection_repo
    )

    await manager.handle_connection()

# --- REST Endpoints --- #

@router.post("/", response_model=CreateChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    chat_in: ChatCreate,
    current_user: UserDep,
    chat_service: ChatServiceDep
) -> CreateChatResponse:
    created_chat = await chat_service.create_new_chat(chat_data=chat_in, owner_id=current_user.id)
    response_data = ChatData.model_validate(created_chat)
    return CreateChatResponse(data=response_data)

@router.get("/", response_model=GetChatsResponse)
async def get_user_chats(
    current_user: UserDep,
    chat_service: ChatServiceDep,
    limit: int = Query(default=20, gt=0, le=100),
    before_timestamp: Optional[datetime] = Query(default=None)
) -> GetChatsResponse:
    """Gets a paginated list of chats for the current user."""
    paginated_chats = await chat_service.get_chats_for_user(
        owner_id=current_user.id, 
        limit=limit,
        before_timestamp=before_timestamp
    )
    return GetChatsResponse(data=paginated_chats)

@router.get("/{chat_id}", response_model=GetChatDetailsResponse)
async def get_chat_details(
    chat_id: PydanticObjectId,
    current_user: UserDep,
    chat_service: ChatServiceDep
) -> GetChatDetailsResponse:
    """Gets basic details for a specific chat (name, dates, etc.), excluding messages."""
    chat = await chat_service.get_chat_by_id(chat_id=chat_id, owner_id=current_user.id)
    response_data = ChatData.model_validate(chat)
    return GetChatDetailsResponse(data=response_data)

@router.patch("/{chat_id}", response_model=GetChatDetailsResponse)
async def update_chat(
    chat_id: PydanticObjectId,
    update_payload: ChatUpdate,
    current_user: UserDep,
    chat_service: ChatServiceDep
) -> GetChatDetailsResponse:
    """Updates the name and/or subtitle of a specific chat."""
    updated_chat = await chat_service.update_chat_details(
        chat_id=chat_id,
        update_data=update_payload,
        owner_id=current_user.id
    )
    response_data = ChatData.model_validate(updated_chat)
    return GetChatDetailsResponse(data=response_data)

@router.get("/{chat_id}/messages", response_model=GetChatMessagesResponse)
async def get_chat_messages(
    chat_id: PydanticObjectId,
    current_user: UserDep,
    chat_service: ChatServiceDep,
    limit: int = Query(default=30, gt=0, le=100),
    before_timestamp: Optional[datetime] = Query(default=None)
) -> GetChatMessagesResponse:
    """Gets a paginated list of messages for a specific chat."""
    paginated_messages = await chat_service.get_messages_for_chat(
        chat_id=chat_id,
        owner_id=current_user.id,
        limit=limit,
        before_timestamp=before_timestamp
    )
    return GetChatMessagesResponse(data=paginated_messages)

@router.post("/{chat_id}/messages", response_model=AddMessageResponse, status_code=status.HTTP_201_CREATED)
async def add_chat_message(
    chat_id: PydanticObjectId,
    message_in: MessageCreate,
    current_user: UserDep,
    chat_service: ChatServiceDep
) -> AddMessageResponse:
    try:
        created_message = await chat_service.add_message_to_chat(
            chat_id=chat_id,
            message_data=message_in,
            current_user_id=current_user.id
        )
        response_data = MessageData.model_validate(created_message)
        return AddMessageResponse(data=response_data)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not add message") 