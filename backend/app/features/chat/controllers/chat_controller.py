from fastapi import APIRouter, HTTPException, status, WebSocket, WebSocketDisconnect
from beanie import PydanticObjectId

# Updated import paths for schemas and services
from ..schemas import (
    ChatCreate, 
    MessageCreate, 
    # Import new response types
    GetChatsResponse, 
    GetChatDetailsResponse, 
    CreateChatResponse, 
    AddMessageResponse
)
from app.config.dependencies import ChatServiceDep, UserDep, ConnectionRepositoryDep

router = APIRouter(
    prefix="/chats",
    tags=["Chat"]
)

# --- WebSocket Endpoint --- #

@router.websocket("/ws/{chat_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    chat_id: str,
    connection_repo: ConnectionRepositoryDep
):
    await connection_repo.connect(websocket, chat_id)
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received WS message in chat {chat_id}: {data}")
    except WebSocketDisconnect:
        connection_repo.disconnect(websocket, chat_id)
        print(f"Client disconnected from chat {chat_id}")
    except Exception as e:
        print(f"Error in WebSocket connection for chat {chat_id}: {e}")
        connection_repo.disconnect(websocket, chat_id)

# --- REST Endpoints --- #

@router.post("/", response_model=CreateChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    chat_in: ChatCreate,
    current_user: UserDep,
    chat_service: ChatServiceDep
) -> CreateChatResponse:
    if not current_user or not current_user.id:
         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    created_chat = await chat_service.create_new_chat(chat_data=chat_in, owner_id=current_user.id)
    return CreateChatResponse(data=created_chat)

@router.get("/", response_model=GetChatsResponse)
async def get_user_chats(
    current_user: UserDep,
    chat_service: ChatServiceDep
) -> GetChatsResponse:
    if not current_user or not current_user.id:
         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    # Service returns List[Chat], response_model handles serialization to ChatData (omitting messages)
    chats = await chat_service.get_chats_for_user(owner_id=current_user.id)
    return GetChatsResponse(data=chats)

@router.get("/{chat_id}", response_model=GetChatDetailsResponse)
async def get_chat_details(
    chat_id: PydanticObjectId,
    current_user: UserDep,
    chat_service: ChatServiceDep
) -> GetChatDetailsResponse:
    if not current_user or not current_user.id:
         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    # Service returns Chat (with messages fetched), response_model handles serialization
    chat = await chat_service.get_chat_by_id(chat_id=chat_id, owner_id=current_user.id)
    # No need for 404 check here if service raises AppException
    return GetChatDetailsResponse(data=chat)

@router.post("/{chat_id}/messages", response_model=AddMessageResponse, status_code=status.HTTP_201_CREATED)
async def add_chat_message(
    chat_id: PydanticObjectId,
    message_in: MessageCreate,
    current_user: UserDep,
    chat_service: ChatServiceDep
) -> AddMessageResponse:
    if not current_user or not current_user.id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

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