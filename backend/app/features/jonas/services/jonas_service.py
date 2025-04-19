import traceback
from typing import TYPE_CHECKING, Optional, Tuple
from beanie import PydanticObjectId
from google.adk.runners import Runner
from google.adk.events import Event
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

# Jonas Agent
from app.agents.jonas_agent import jonas_agent, JONAS_NAME

if TYPE_CHECKING:
    from app.features.chat.models import Chat, Message
    from app.features.chat.services import ChatService, WebSocketService
    from app.features.chat.repositories import ChatRepository

from .chat_history_session_service import ChatHistoryLoader 

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
            app_name=JONAS_NAME,
            session_service=self.session_service
        )
        # --- End ADK Setup --- #

    async def load_session(self, chat: "Chat", user_id: PydanticObjectId):
        """Loads history into a session and stores invocation IDs in state."""
        session_id = str(chat.id)
        user_id_str = str(user_id)

        session_obj = self.session_service.get_session(
            app_name=JONAS_NAME, user_id=user_id_str, session_id=session_id
        )
        if session_obj is None:
            session_obj = self.session_service.create_session(
                app_name=JONAS_NAME, user_id=user_id_str, session_id=session_id, state={}
            )
        
        # --- Store Invocation IDs in State --- 
        # Use distinct keys to avoid potential clashes
        state_user_id_key = "invocation_user_id"
        state_session_id_key = "invocation_session_id"
        session_obj.state[state_user_id_key] = user_id_str
        session_obj.state[state_session_id_key] = session_id
        print(f"JonasService load_session: Stored IDs in state: UserKey='{state_user_id_key}', SessionKey='{state_session_id_key}'")
        # --- End Storing IDs --- 

        # --- Load History --- 
        adk_events = await self.history_loader.get_adk_formatted_events(chat.id)
        # Replace history instead of appending if appropriate
        session_obj.events = adk_events
        print(f"JonasService load_session: Loaded {len(adk_events)} history events.")
        # --- End Load History --- 

    # --- Event Handler Methods --- #

    async def _handle_streaming_chunk(
        self,
        event: Event,
        chat: "Chat",
        session_id: str,
        agent_message_id: Optional[PydanticObjectId],
        accumulated_content: str
    ) -> Tuple[Optional[PydanticObjectId], str]:
        """Handles a streaming text chunk event."""
        chunk = event.content.parts[0].text
        accumulated_content += chunk
        new_agent_message_id = agent_message_id

        if agent_message_id is None: # Create DB message on first chunk
            agent_msg_model: Optional["Message"] = await self.chat_service._create_and_broadcast_message(
                chat=chat,
                sender_type='agent',
                content="", # Start empty
                message_type='text',
            )
            if agent_msg_model:
                new_agent_message_id = agent_msg_model.id
            else:
                print(f"JonasService Error: Failed to create initial agent message DB entry for chat {chat.id}")
                # Consider how to signal failure if needed

        # Broadcast chunk update only if we have a message ID
        if new_agent_message_id:
            await self.websocket_service.broadcast_message_update(
                chat_id=session_id,
                message_id=str(new_agent_message_id),
                chunk=chunk,
                is_error=False
            )
        
        return new_agent_message_id, accumulated_content

    async def _handle_delegation_signal(self, event: Event, chat: "Chat"):
        """Handles a delegation signal event."""
        print(f"JonasService: Detected delegation to {event.actions.transfer_to_agent}. Broadcasting action message.")
        await self.chat_service._create_and_broadcast_message(
            chat=chat,
            sender_type='agent',
            content=f"Delegating to {event.actions.transfer_to_agent}...", # More dynamic content
            message_type='action', 
            tool_name=event.actions.transfer_to_agent # Store agent name
        )

    def _handle_tool_call_request(self, event: Event):
        """Handles a tool call request event (logging only)."""
        function_calls = event.get_function_calls()
        for call in function_calls:
            # Avoid logging the delegation function call itself as a "tool use"
            if call.name != 'transfer_to_agent':
                print(f"JonasService: Agent '{event.author}' requested tool '{call.name}' (handled by Runner). Args: {call.args}")

    def _handle_tool_result(self, event: Event):
        """Handles a tool result event (logging only)."""
        function_responses = event.get_function_responses()
        for resp in function_responses:
            print(f"JonasService: Received result for tool '{resp.name}' (processed by Runner). Result: {resp.response}")

    async def _handle_final_response(
        self,
        event: Event,
        chat: "Chat",
        session_id: str,
        agent_message_id: Optional[PydanticObjectId],
        accumulated_content: str
    ) -> Tuple[str, bool]:
        """Handles the final response event."""
        print(f"JonasService: Final response event received for session {session_id}.")
        final_text = None
        if event.content and event.content.parts and event.content.parts[0].text:
            final_text = event.content.parts[0].text
            if agent_message_id and not event.partial: # Part of stream
                accumulated_content += final_text
            elif not agent_message_id: # Whole message is in this final event
                accumulated_content = final_text

        if agent_message_id:
            await self.websocket_service.broadcast_stream_end(
                chat_id=session_id,
                message_id=str(agent_message_id)
            )
            if accumulated_content:
                await self.chat_service.update_message_content(agent_message_id, accumulated_content)
                print(f"JonasService: Updated final content for message {agent_message_id}")
            else:
                print(f"JonasService: Final response for message {agent_message_id} had no text content to update.")
        elif accumulated_content: # Final response is the only content (no stream)
            print(f"JonasService: Final response is the only content. Creating single message.")
            await self.chat_service._create_and_broadcast_message(
                chat=chat,
                sender_type='agent',
                content=accumulated_content,
                message_type='text',
            )
        else:
            print(f"JonasService: Final response event had no text content and no prior stream.")
        
        return accumulated_content, True # Return final accumulated content and signal loop break

    async def _handle_error_event(self, event: Event, chat: "Chat", session_id: str):
        """Handles an explicit error event from the ADK runner."""
        print(f"JonasService: Received error event: {event.error_code} - {event.error_message}")
        # Consider broadcasting a specific error message
        await self.chat_service._create_and_broadcast_message(
            chat=chat,
            sender_type='agent',
            content=f"Agent Error: {event.error_message}" if event.error_message else "An agent error occurred.",
            message_type='error'
        )

    # --- Main Processing Method --- #

    async def process_chat_message(self, chat: "Chat", user_content: str, user_id: PydanticObjectId):
        """Processes a user message using the ADK Runner and broadcasts events based on ADK patterns."""
        agent_message_id: Optional[PydanticObjectId] = None
        accumulated_content = ""
        session_id = str(chat.id) # Use chat ID as session ID for ADK
        user_id_str = str(user_id) # Runner expects string IDs
        should_break_loop = False

        try:
            # --- Session Management & History Loading --- 
            await self.load_session(chat, user_id) # This now also stores IDs in state
            print(f"JonasService: Session loaded/updated (History & State IDs) for {session_id}")
            # --- End Session Management & History Loading ---

            # --- Prepare User Message for ADK Runner --- 
            # REMOVED: No longer need to prepend context here
            # context_header = f"INTERNAL_CONTEXT_BLOCK: user_id_str='{user_id_str}' chat_id_str='{session_id}' END_CONTEXT_BLOCK\n\n"
            # full_user_content = context_header + user_content
            content = genai_types.Content(role='user', parts=[genai_types.Part(text=user_content)]) # Pass original user content

            # --- ADK Runner Event Loop --- 
            async for event in self.runner.run_async(user_id=user_id_str, session_id=session_id, new_message=content):
                
                # --- Event Processing Logic --- 
                if event.partial and event.content and event.content.parts and event.content.parts[0].text:
                    agent_message_id, accumulated_content = await self._handle_streaming_chunk(
                        event, chat, session_id, agent_message_id, accumulated_content
                    )
                elif event.actions and event.actions.transfer_to_agent:
                    await self._handle_delegation_signal(event, chat)
                elif event.get_function_calls():
                    self._handle_tool_call_request(event)
                elif event.get_function_responses():
                    self._handle_tool_result(event)
                elif event.is_final_response():
                    accumulated_content, should_break_loop = await self._handle_final_response(
                        event, chat, session_id, agent_message_id, accumulated_content
                    )
                elif event.error_code or event.error_message:
                    await self._handle_error_event(event, chat, session_id)
                # Add other conditions for different event types if necessary

                if should_break_loop:
                    break
            # --- End ADK Runner Event Loop --- 

        except Exception as e:
            print(f"JonasService: Error during Runner execution observation for session {session_id}: {e}")
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
        finally:
             pass # No specific finally action needed 