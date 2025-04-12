from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, WebSocketException, Query
from fastapi.websockets import WebSocketState
from beanie import PydanticObjectId
from pydantic import ValidationError
from datetime import datetime
from typing import Optional
from ..schemas import ChatData, MessageData
from .websocket_controller import WebSocketController
from app.features.common.exceptions import AppException
import traceback
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
from app.config.dependencies import (
    ChatServiceDep, 
    UserDep, 
    WebSocketRepositoryDep,
    CurrentUserWsDep,
    AgentServiceDep
)

router = APIRouter(
    prefix="/chats",
    tags=["Chat"]
)

# --- WebSocket Endpoint --- #

@router.websocket("/ws/{chat_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    chat_id: str,
    websocket_repository: WebSocketRepositoryDep,
    current_user: CurrentUserWsDep,
    chat_service: ChatServiceDep,
    agent_service: AgentServiceDep
):
    """Handles WebSocket connection setup and teardown, delegates processing to WebSocketController."""
    try:
        chat_id_obj = PydanticObjectId(chat_id)
    except Exception:
        # Close immediately if chat_id is invalid
        await websocket.accept() # Need to accept before closing with code
        await websocket.close(code=status.WS_1007_INVALID_FRAMEWORK_PAYLOAD_DATA, reason="Invalid chat ID format")
        return

    # Create an instance of the controller for this connection
    controller = WebSocketController(
        websocket=websocket,
        chat_id_obj=chat_id_obj,
        current_user=current_user,
        websocket_repository=websocket_repository,
        chat_service=chat_service,
        agent_service=agent_service
    )

    await controller.handle_connect()

    try:
        # Run the main message processing loop
        await controller.run_message_loop()
    except Exception as e:
        print(f"WS Endpoint: Unhandled exception from controller loop for chat {chat_id}: {e}")
        if websocket.client_state != WebSocketState.DISCONNECTED:
            try:
                 await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
            except RuntimeError:
                 pass # Already closed
    finally:
        controller.handle_disconnect()

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
    limit: int = Query(default=20, gt=0, le=100),
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
    """Adds a message (sent via REST) to a chat, saves, and broadcasts."""
    try:
        # 1. Find the chat and verify ownership
        chat = await chat_service.chat_repository.find_chat_by_id_and_owner(chat_id, current_user.id)
        if not chat:
            chat_exists = await chat_service.chat_repository.find_chat_by_id(chat_id)
            if chat_exists:
                 raise AppException(status_code=403, error_code="FORBIDDEN", message="User does not own this chat")
            else:
                 raise AppException(status_code=404, error_code="CHAT_NOT_FOUND", message="Chat not found")

        # Determine author_id (should always be the current user for REST endpoint)
        author_id: Optional[PydanticObjectId] = None
        if message_in.sender_type == 'user':
            author_id = current_user.id
        else:
             # Prevent agent messages from being added via this REST endpoint?
             # Or allow if needed, but without specific author_id? For now, assume user only.
             raise AppException(status_code=400, error_code="INVALID_SENDER", message="Only user messages can be added via this endpoint.")

        # 2. Use the internal helper to create, save, and broadcast
        created_message = await chat_service._create_and_broadcast_message(
            chat=chat,
            sender_type=message_in.sender_type, # Should be 'user'
            content=message_in.content,
            message_type='text', # Assume 'text' for REST messages
            author_id=author_id
        )

        # Handle case where _create_and_broadcast_message might return None
        # (though it shouldn't for saveable types like 'text')
        if not created_message:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to process message creation.")
            
        # 3. Prepare and return the response
        response_data = MessageData.model_validate(created_message)
        return AddMessageResponse(data=response_data)
        
    except AppException as e: # Catch specific AppExceptions first
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except HTTPException as e:
        raise e # Re-raise other HTTP exceptions
    except Exception as e:
        print(f"REST add_chat_message Error: {e}")
        traceback.print_exc() # Log the full traceback
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not add message") 