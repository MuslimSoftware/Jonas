import traceback
from typing import TYPE_CHECKING, Optional, Tuple
from beanie import PydanticObjectId
from google.adk.runners import Runner
from google.adk.events import Event
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

# Jonas Agent
from app.agents.jonas_agent import jonas_agent

if TYPE_CHECKING:
    from app.features.chat.models import Chat
    from app.features.chat.services import ChatService, WebSocketService
    from app.features.chat.repositories import ChatRepository

from .chat_history_session_service import ChatHistoryLoader 

ADK_APP_NAME = "jonas_ai_agent"

class JonasService:
    """Service layer for handling Jonas agent interactions using ADK Runner."""

    def __init__(
        self,
        chat_service: "ChatService",
        websocket_service: "WebSocketService",
        chat_repository: "ChatRepository"
    ):
        self.chat_service = chat_service
        self.websocket_service = websocket_service
        self.chat_repository = chat_repository

        self.history_loader = ChatHistoryLoader(chat_repository=self.chat_repository)
        # --- ADK Setup --- #
        self.session_service = InMemorySessionService()
        self.runner = Runner(
            agent=jonas_agent,
            app_name=ADK_APP_NAME,
            session_service=self.session_service
        )
        # --- End ADK Setup --- #

    async def load_session(self, chat: "Chat", user_id: PydanticObjectId):
        """Loads a session from the InMemorySessionService."""
        session_id = str(chat.id)
        user_id_str = str(user_id)

        session_obj = self.session_service.get_session(
            app_name=ADK_APP_NAME, user_id=user_id_str, session_id=session_id
        )
        if session_obj is None:
            session_obj = self.session_service.create_session(
                app_name=ADK_APP_NAME, user_id=user_id_str, session_id=session_id, state={}
            )

        adk_events = await self.history_loader.get_adk_formatted_events(chat.id)
        for event in adk_events:
            self.session_service.append_event(session_obj, event)

    async def handle_text_message(
        self, 
        event: Event, 
        chat: "Chat", 
        session_id: str, 
        agent_message_id: Optional[PydanticObjectId], 
        current_accumulated_content: str
    ) -> Tuple[Optional[PydanticObjectId], str]:
        """Handles text chunks, creates initial message, broadcasts updates."""
        new_accumulated_content = current_accumulated_content
        current_agent_message_id = agent_message_id

        # Process text content regardless of final response marker here
        if not event.content or not event.content.parts:
            return current_agent_message_id, new_accumulated_content

        chunk = event.content.parts[0].text
        if chunk:
            new_accumulated_content += chunk

            if current_agent_message_id is None:
                agent_msg_model = await self.chat_service._create_and_broadcast_message(
                    chat=chat,
                    sender_type='agent',
                    content="", # Start empty
                    message_type='text',
                )
                if agent_msg_model:
                    current_agent_message_id = agent_msg_model.id
                else:
                    print(f"JonasService: Error - Failed to create initial agent message DB entry for chat {chat.id}")
                    return current_agent_message_id, new_accumulated_content 

            if current_agent_message_id:
                await self.websocket_service.broadcast_message_update(
                    chat_id=session_id,
                    message_id=str(current_agent_message_id),
                    chunk=chunk,
                    is_error=False
                )
                
        return current_agent_message_id, new_accumulated_content

    async def handle_tool_request(self, event: Event, chat: "Chat"):
        """Processes a tool request event (shows 'Using tool...')."""
        # This handles the request *before* execution by the Runner
        if not event.actions or not hasattr(event.actions, 'tool_code') or not event.actions.tool_code:
            return

        tool_name = "unknown_tool" # Placeholder
        # Structure might differ slightly with sub-agents, but principle is the same
        if hasattr(event.actions.tool_code[0], 'function_call'): 
            tool_name = event.actions.tool_code[0].function_call.name
        
        print(f"JonasService: Agent requested tool '{tool_name}' (handled by Runner/SubAgent)")
        await self.chat_service._create_and_broadcast_message(
            chat=chat,
            sender_type='agent',
            content=f"Using tool: {tool_name}", # Original message
            message_type='tool_use',
            tool_name=tool_name
        )

    async def handle_final_response(
        self, 
        event: Event, 
        chat: "Chat", 
        session_id: str, 
        agent_message_id: Optional[PydanticObjectId], 
        final_accumulated_content: str
    ) -> bool:
        """Processes a final response event."""
        if not event.is_final_response():
            return False

        # Handle potential final text content within the final event
        final_chunk = None
        final_content_for_db = final_accumulated_content
        if event.content and event.content.parts:
            final_chunk = event.content.parts[0].text
            # Avoid double-counting if last chunk was already processed by handle_text_message
            # This check might be imperfect depending on timing.
            if final_chunk and not final_accumulated_content.endswith(final_chunk):
                final_content_for_db += final_chunk
        
        if agent_message_id:
            # Send final chunk update only if it changed the content for DB
            if final_chunk and final_content_for_db != final_accumulated_content:
                 await self.websocket_service.broadcast_message_update(
                    chat_id=session_id,
                    message_id=str(agent_message_id),
                    chunk=final_chunk,
                    is_error=False
                )

            # Broadcast STREAM_END
            await self.websocket_service.broadcast_stream_end(
                chat_id=session_id,
                message_id=str(agent_message_id)
            )
            # Update the full message content in DB
            if final_content_for_db:
                await self.chat_service.update_message_content(agent_message_id, final_content_for_db)
            # Maybe delete the message if content is empty? Optional.
        elif final_content_for_db: # Handle case where final response is the *only* response
            # Create the message and broadcast it as a single unit 
            await self.chat_service._create_and_broadcast_message(
                chat=chat,
                sender_type='agent',
                content=final_content_for_db,
                message_type='text',
            )
        else:
            # Final response marker but no text content at all
            print(f"JonasService: Final response event for {session_id} had no text content.")
            # Send STREAM_END only if a message placeholder was created (e.g., for tool use)
            if agent_message_id: 
                await self.websocket_service.broadcast_stream_end(
                    chat_id=session_id,
                    message_id=str(agent_message_id)
                )
        return True

    async def process_chat_message(self, chat: "Chat", user_content: str, user_id: PydanticObjectId):
        """Processes a user message using the ADK Runner and broadcasts events."""
        agent_message_id: Optional[PydanticObjectId] = None
        session_id = str(chat.id)
        user_id_str = str(user_id)
        # Keep accumulated_content local to this method
        accumulated_content: str = "" 

        try:
            await self.load_session(chat, user_id)
            
            content = genai_types.Content(role='user', parts=[genai_types.Part(text=user_content)])
            async for event in self.runner.run_async(
                user_id=user_id_str, 
                session_id=session_id, 
                new_message=content 
            ):
                # Update accumulated_content and agent_message_id from handler
                agent_message_id, accumulated_content = await self.handle_text_message(
                    event, chat, session_id, agent_message_id, accumulated_content
                )
                
                # Handle tool request display message (Runner handles actual execution)
                await self.handle_tool_request(event, chat)
                
                # Pass final accumulated content to final handler
                if await self.handle_final_response(event, chat, session_id, agent_message_id, accumulated_content):
                    break

        except Exception as e:
            print(f"JonasService: Error during Runner execution for session {session_id}: {e}")
            traceback.print_exc()
            try:
                error_content = "An internal error occurred while processing your request with the agent."
                await self.chat_service._create_and_broadcast_message(
                    chat=chat,
                    sender_type='agent',
                    content=error_content,
                    message_type='error',
                )
            except Exception as broadcast_err:
                print(f"JonasService: Failed to broadcast error message for chat {session_id}: {broadcast_err}")
        finally:
             pass # No specific finally action needed 