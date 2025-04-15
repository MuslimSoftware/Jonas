import traceback
from typing import TYPE_CHECKING, Optional, Tuple
from beanie import PydanticObjectId
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService # Using in-memory for now
from google.genai import types as genai_types # For creating content messages

# Jonas Agent
from app.features.jonas.agent import jonas_agent

if TYPE_CHECKING:
    from app.features.chat.models import Chat
    from app.features.chat.services import ChatService, WebSocketService
    from app.features.agent.services import BrowserAgentService
    from app.features.jonas.repositories import JonasRepository
    from app.features.user.models import User

# Define a consistent app name for the runner/sessions
ADK_APP_NAME = "jonas_ai_agent"

class JonasService:
    """Service layer for handling Jonas agent interactions using ADK Runner."""

    def __init__(
        self,
        # Keep dependencies needed by methods or potentially by tools/callbacks
        jonas_repository: "JonasRepository",
        chat_service: "ChatService",
        websocket_service: "WebSocketService",
        browser_agent_service: "BrowserAgentService",
    ):
        self.jonas_repository = jonas_repository
        self.chat_service = chat_service
        self.websocket_service = websocket_service
        self.browser_agent_service = browser_agent_service # Keep for tool execution if needed

        # --- ADK Setup --- #
        # For now, use simple in-memory session management
        # TODO: Replace with a persistent SessionService (e.g., Redis, DB)
        self.session_service = InMemorySessionService()

        # Initialize the ADK Runner with the agent and session service
        self.runner = Runner(
            agent=jonas_agent, # The root agent definition
            app_name=ADK_APP_NAME, # A name for this application context
            session_service=self.session_service
        )
        # --- End ADK Setup --- #

    # Removed _handle_text_event and _handle_tool_request_event

    async def process_chat_message(self, chat: "Chat", user_content: str, user_id: PydanticObjectId):
        """Processes a user message using the ADK Runner and broadcasts events."""
        agent_message_id: Optional[PydanticObjectId] = None
        accumulated_content = ""
        session_id = str(chat.id) # Use chat ID as session ID for ADK
        user_id_str = str(user_id) # Runner expects string IDs

        try:
            # Ensure session exists by calling create_session before run_async
            # InMemorySessionService might just overwrite if it exists, which is fine here.
            self.session_service.create_session(
                app_name=ADK_APP_NAME,
                user_id=user_id_str,
                session_id=session_id
                # Add initial state here if needed: state={...}
            )
            # Remove explicit session get/create - Runner handles this
            # session = self.session_service.get_session(ADK_APP_NAME, user_id_str, session_id)

            # Prepare the user message
            content = genai_types.Content(role='user', parts=[genai_types.Part(text=user_content)])

            # Use the Runner to handle the agent interaction
            async for event in self.runner.run_async(user_id=user_id_str, session_id=session_id, new_message=content):
                # --- Text Chunk Handling --- 
                # Check if the event has content, likely a text chunk from the LLM
                # We also check it's NOT the final response to avoid double-counting
                if event.content and event.content.parts and not event.is_final_response():
                    chunk = event.content.parts[0].text # Assuming text is in the first part
                    if chunk: # Ensure there's actually text content
                        accumulated_content += chunk

                        if agent_message_id is None: # Create message on first text chunk
                            agent_msg_model = await self.chat_service._create_and_broadcast_message(
                                chat=chat,
                                sender_type='agent',
                                content="",
                                message_type='text',
                            )
                            if agent_msg_model:
                                agent_message_id = agent_msg_model.id
                            else:
                                print(f"JonasService: Error - Failed to create initial agent message DB entry for chat {chat.id}")
                                return # Abort if DB write fails

                        # Broadcast the chunk update if we have an ID
                        if agent_message_id:
                            await self.websocket_service.broadcast_message_update(
                                chat_id=session_id,
                                message_id=str(agent_message_id),
                                chunk=chunk,
                                is_error=False
                            )

                # --- Tool Request Handling --- 
                # Check if the event has actions, which might indicate a tool call
                # The exact structure needs verification, this is based on common patterns
                # Look for tool_code or similar within actions
                # TODO: Verify the exact event structure for tool calls from ADK runner events
                if event.actions and hasattr(event.actions, 'tool_code') and event.actions.tool_code:
                     # Runner handles calling the tool. We just broadcast the intent.
                     # Extract tool name - this might need adjustment based on actual event structure
                     tool_name = "unknown_tool" # Placeholder
                     if hasattr(event.actions.tool_code[0], 'function_call'): # Example structure
                         tool_name = event.actions.tool_code[0].function_call.name
                     
                     print(f"JonasService: Agent requested tool '{tool_name}' (handled by Runner)")
                     await self.chat_service._create_and_broadcast_message(
                         chat=chat,
                         sender_type='agent',
                         content=f"Using tool: {tool_name}",
                         message_type='tool_use',
                         tool_name=tool_name
                     )
                     # Tool execution is handled by the Runner

                # --- Final Response Handling --- 
                if event.is_final_response():
                    # Handle potential final text content (might arrive in the final event too)
                    final_chunk = None
                    if event.content and event.content.parts:
                        final_chunk = event.content.parts[0].text
                    
                    if agent_message_id:
                        # If there was final text different from accumulated, send one last update
                        if final_chunk and final_chunk != accumulated_content: 
                             await self.websocket_service.broadcast_message_update(
                                chat_id=session_id,
                                message_id=str(agent_message_id),
                                chunk=final_chunk,
                                is_error=False
                            )
                             accumulated_content = final_chunk # Update accumulated for DB save
                        
                        # Broadcast STREAM_END
                        await self.websocket_service.broadcast_stream_end(
                            chat_id=session_id,
                            message_id=str(agent_message_id)
                        )
                        # Update the full message content in DB
                        if accumulated_content:
                            await self.chat_service.update_message_content(agent_message_id, accumulated_content)
                    elif final_chunk: # Handle case where final response is the *only* response (no prior chunks)
                        # Create the message and broadcast it as a single unit (no stream needed)
                         await self.chat_service._create_and_broadcast_message(
                            chat=chat,
                            sender_type='agent',
                            content=final_chunk,
                            message_type='text',
                        )
                    else:
                        # Handle cases where there's a final response marker but no text (e.g., after tool error?) 
                        print(f"JonasService: Final response event for {session_id} had no text content.")
                        # If we had an agent_message_id from a tool use, send STREAM_END
                        if agent_message_id: 
                             await self.websocket_service.broadcast_stream_end(
                                chat_id=session_id,
                                message_id=str(agent_message_id)
                            )

                    # Stop processing events for this turn once final response is handled
                    break

        except Exception as e:
            print(f"JonasService: Error during Runner execution for session {session_id}: {e}")
            traceback.print_exc()
            # Attempt to create/broadcast an error message
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