from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, WebSocketException
from beanie import PydanticObjectId

from ..schemas import (
    ChatCreate, 
    MessageCreate, 
    GetChatsResponse, 
    GetChatDetailsResponse, 
    CreateChatResponse, 
    AddMessageResponse
)
from app.config.dependencies import ChatServiceDep, UserDep, ConnectionRepositoryDep, CurrentUserWsDep
from app.features.user.models import User
from ..schemas import ChatData, MessageData

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

    await connection_repo.connect(websocket, chat_id)
    print(f"User {current_user.id} connected to chat {chat_id}")

    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received WS message from {current_user.id} in chat {chat_id}: {data}")
            
            try:
                message_in = MessageCreate.model_validate_json(data)
                
                await chat_service.add_message_to_chat(
                    chat_id=chat_id_obj,
                    message_data=message_in,
                    current_user_id=current_user.id
                )
            except ValidationError as e:
                print(f"WS validation error for user {current_user.id} in chat {chat_id}: {e}")
            except Exception as e:
                print(f"Error processing WS message from {current_user.id} in chat {chat_id}: {e}")

    except WebSocketDisconnect:
        print(f"User {current_user.id} disconnected from chat {chat_id}")
    except Exception as e:
        print(f"Error in WebSocket loop for user {current_user.id} in chat {chat_id}: {e}")
    finally:
        connection_repo.disconnect(websocket, chat_id)
        print(f"Cleaned up connection for user {current_user.id} from chat {chat_id}")

# --- REST Endpoints --- #

@router.post("/", response_model=CreateChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    chat_in: ChatCreate,
    current_user: UserDep,
    chat_service: ChatServiceDep
) -> CreateChatResponse:
    created_chat = await chat_service.create_new_chat(chat_data=chat_in, owner_id=current_user.id)
    return CreateChatResponse(data=created_chat)

@router.get("/", response_model=GetChatsResponse)
async def get_user_chats(
    current_user: UserDep,
    chat_service: ChatServiceDep
) -> GetChatsResponse:
    chats = await chat_service.get_chats_for_user(owner_id=current_user.id)
    return GetChatsResponse(data=chats)

@router.get("/{chat_id}", response_model=GetChatDetailsResponse)
async def get_chat_details(
    chat_id: PydanticObjectId,
    current_user: UserDep,
    chat_service: ChatServiceDep
) -> GetChatDetailsResponse:
    chat = await chat_service.get_chat_by_id(chat_id=chat_id, owner_id=current_user.id)
    return GetChatDetailsResponse(data=chat)

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
        return AddMessageResponse(data=created_message)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not add message") 