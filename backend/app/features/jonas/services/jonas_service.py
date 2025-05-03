import traceback
from typing import TYPE_CHECKING, Optional, Tuple, Any
from beanie import PydanticObjectId
from google.adk.runners import Runner
from google.adk.events import Event
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types
import json
import logging

# Jonas Agent - Import agent instance directly
from app.agents.jonas_agent import jonas_agent

# Import ContextService only for type checking
from app.features.chat.services import ContextService

if TYPE_CHECKING:
    from app.features.chat.models import Chat, Message
    from app.features.chat.services import ChatService, WebSocketService
    from app.features.chat.repositories import ChatRepository

from .chat_history_session_service import ChatHistoryLoader 

logger = logging.getLogger(__name__)

class JonasService:
    """Service layer for handling Jonas agent interactions using ADK Runner."""

    def __init__(
        self,
        chat_service: "ChatService",
        websocket_service: "WebSocketService",
        chat_repository: "ChatRepository",
        context_service: "ContextService"
    ):
        self.chat_service = chat_service
        self.websocket_service = websocket_service
        self.chat_repository = chat_repository
        # Store context service
        self.context_service = context_service

        self.history_loader = ChatHistoryLoader(chat_repository=self.chat_repository)
        # --- ADK Setup --- #
        self.session_service = InMemorySessionService()
        self.runner = Runner(
            agent=jonas_agent,
            app_name="Jonas",
            session_service=self.session_service
        )
        # --- End ADK Setup --- #

    async def load_session(self, chat: "Chat", user_id: PydanticObjectId):
        """Loads history into a session and stores invocation IDs in state."""
        session_id = str(chat.id)
        user_id_str = str(user_id)

        # --- Prepare Initial State (including context) --- 
        # Base state needed by the runner/agent
        initial_state = {
            "invocation_user_id": user_id_str,
            "invocation_session_id": session_id
        }

        # Fetch and format context items
        context_items = await self.context_service.fetch_all_chat_context(chat.id)
        print(f"DEBUG: Fetched {len(context_items)} context items for chat {chat.id}.") # Use print
        # Initialize the top-level context structure
        formatted_context_state = {'context': {}}
        for item in context_items:
            # Ensure source agent sub-dictionary exists
            if item.source_agent not in formatted_context_state['context']:
                formatted_context_state['context'][item.source_agent] = {}

            # Assign the data under source_agent -> content_type
            # Sorting ensures the latest item for a given source/type wins
            formatted_context_state['context'][item.source_agent][item.content_type] = item.data

        # Merge formatted context into the initial state
        initial_state.update(formatted_context_state)
        # --- End Prepare Initial State --- 

        # Print initial state only when creating a new session
        session_obj = self.session_service.get_session(
            app_name="Jonas", user_id=user_id_str, session_id=session_id
        )
        if session_obj is None:
            context_key_count = sum(len(types) for types in formatted_context_state.get('context', {}).values())
            print(f"DEBUG: Creating new session {session_id} with initial state including {context_key_count} context items under the 'context' key.")
            print(f"DEBUG: Initial state for session {session_id}: {initial_state}") # Use print
            session_obj = self.session_service.create_session(
                app_name="Jonas",
                user_id=user_id_str,
                session_id=session_id,
                state=initial_state # Use the prepared state with context
            )
        else:
            print(f"DEBUG: Found existing session {session_id}. Not overwriting state.")

        # --- Load History --- 
        adk_events = await self.history_loader.get_adk_formatted_events(chat.id)
        for event in adk_events:
            self.session_service.append_event(session_obj, event)
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

    async def _handle_tool_result(self, event: Event, chat_id: PydanticObjectId):
        """Handles a tool result event by logging it and saving each function response as context."""
        function_responses = event.get_function_responses()
        source_agent = event.author
 
        print(f"--- Handling Tool Result for Chat {chat_id} ---")
        print(f"DEBUG: Full Event Object: {event}") # Print the whole event
        for resp in function_responses:
            print(f"DEBUG: Received result for tool '{resp.name}' from '{source_agent}'. Raw Response: {resp.response}") # Use print
 
            # --- Updated Extraction Logic ---
            # Handle specific wrapper format {'status': ..., 'data': ...} first
            actual_tool_output = None
            if isinstance(resp.response, dict) and 'status' in resp.response and 'data' in resp.response:
                 actual_tool_output = resp.response.get('data')
            # Fallback for other dictionary responses (try 'result')
            elif isinstance(resp.response, dict):
                 actual_tool_output = resp.response.get('result')
                 # If 'result' key not found, use the dictionary itself as output
                 if actual_tool_output is None:
                      actual_tool_output = resp.response
            # Handle non-dictionary responses directly
            else:
                 actual_tool_output = resp.response
            # --- End Updated Extraction Logic ---
 
            print(f"DEBUG: Extracted actual tool output: {actual_tool_output}") # Use print
 
            # Parse JSON if possible
            parsed_output = actual_tool_output
            if isinstance(parsed_output, str):
                try:
                    parsed_output = json.loads(parsed_output)
                    print("DEBUG: Successfully parsed tool output as JSON.") # Use print
                except json.JSONDecodeError:
                    # Leave as string if not valid JSON
                    print("DEBUG: Tool output is a string but not valid JSON.") # Use print
                    pass
            elif isinstance(parsed_output, dict):
               print("DEBUG: Tool output is already a dictionary.") # Use print
            else:
               print(f"DEBUG: Tool output type is {type(parsed_output)}. Wrapping in dict.") # Use print
 
            # Save the raw response: dict responses directly, wrap non-dict under 'value'
            print(f"DEBUG: Parsed output before potential wrapping: {parsed_output}") # Print parsed data
            context_data = parsed_output if isinstance(parsed_output, dict) else {'value': parsed_output}
            print(f"DEBUG: Final context_data to be saved: {context_data}") # Print final data for saving
 
            print(f"DEBUG: Preparing to save context. Chat ID: {chat_id}, Source: {source_agent}, Type: {resp.name}, Data: {context_data}") # Use print
            await self.context_service.save_agent_context(
                chat_id=chat_id,
                source_agent=source_agent,
                content_type=resp.name,
                data=context_data
            )
 
            print(f"DEBUG: Context save attempt complete for tool '{resp.name}'.") # Use print
 
        print(f"--- Handling Tool Result Complete for Chat {chat_id} ---") # Use print
 
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
        print(f"JonasService: Final response event: {event}")
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
        chat_id_obj = chat.id # Keep the PydanticObjectId for saving context
        user_id_str = str(user_id) # Runner expects string IDs
        should_break_loop = False

        try:
            # --- Session Management & History Loading --- 
            await self.load_session(chat, user_id)
            # --- End Session Management & History Loading ---

            # --- Prepare User Message for ADK Runner --- 
            content = genai_types.Content(role='user', parts=[genai_types.Part(text=user_content)]) # Pass original user content

            # --- ADK Runner Event Loop --- 
            async for event in self.runner.run_async(user_id=user_id_str, session_id=session_id, new_message=content):
                print(f"DEBUG: Received Event Type: {type(event)}, Author: {event.author}, Content: {event.content}, Actions: {event.actions}") # Log every event
                # --- Event Processing Logic --- 
                function_responses = event.get_function_responses()
                tool_results_in_delta = event.actions.state_delta.get('tool_result') # Check state delta

                if event.partial and event.content and event.content.parts and event.content.parts[0].text:
                    agent_message_id, accumulated_content = await self._handle_streaming_chunk(
                        event, chat, session_id, agent_message_id, accumulated_content
                    )
                elif event.actions and event.actions.transfer_to_agent:
                    await self._handle_delegation_signal(event, chat)
                elif event.get_function_calls():
                    self._handle_tool_call_request(event)
                # --- Modified Tool Result Handling --- 
                elif function_responses: 
                    print("DEBUG: Processing tool result via get_function_responses()")
                    # Pass chat_id to the handler
                    await self._handle_tool_result(event, chat_id_obj)
                elif tool_results_in_delta: # Handle result from state delta if not in function_responses
                    print("DEBUG: Processing tool result via state_delta['tool_result']")
                    # Reconstruct a similar event structure for _handle_tool_result if needed,
                    # or adapt _handle_tool_result to accept delta directly.
                    # For now, let's adapt _handle_tool_result (simpler)
                    await self._handle_tool_result_from_delta(tool_results_in_delta, event.author, chat_id_obj)
                # --- End Modified Tool Result Handling ---
                elif event.is_final_response():
                    # Check if this final response is from the database_agent and ignore its text content
                    if event.author == 'database_agent':
                        print("DEBUG: Ignoring final response text from database_agent as per instructions.")
                        # We still might need to update our own agent_message_id state if DB agent was streaming (unlikely now)
                        if agent_message_id:
                            await self.websocket_service.broadcast_stream_end(
                                chat_id=session_id,
                                message_id=str(agent_message_id)
                            )
                            # Don't update content with DB agent's final words
                        should_break_loop = True # Assume DB agent's turn is done
                    else: # Handle final response from Jonas or other agents normally
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

    # New handler for results found in state_delta
    async def _handle_tool_result_from_delta(self, tool_result_data: Any, source_agent: str, chat_id: PydanticObjectId):
        print(f"--- Handling Tool Result From Delta for Chat {chat_id} ---")
        # Assuming tool_result_data directly contains the raw response (e.g., {'status': ..., 'result': ...})
        # We need to know the 'tool name' (content_type) - let's assume it's query_sql_database for now if from DB agent
        # This is a limitation - ideally the delta would include the tool name.
        tool_name = "query_sql_database" if source_agent == "database_agent" else "unknown_tool"
        print(f"DEBUG: Received delta result for tool '{tool_name}' from '{source_agent}'. Raw Response: {tool_result_data}")

        # Reuse extraction logic (might need slight adaptation if structure differs)
        actual_tool_output = None
        if isinstance(tool_result_data, dict) and 'status' in tool_result_data and 'result' in tool_result_data:
             actual_tool_output = tool_result_data.get('result')
        elif isinstance(tool_result_data, dict):
             actual_tool_output = tool_result_data # Use dict itself if no 'result' key
        else:
             actual_tool_output = tool_result_data
        print(f"DEBUG: Extracted actual tool output from delta: {actual_tool_output}")

        # Reuse parsing logic
        parsed_output = actual_tool_output
        if isinstance(parsed_output, str):
            try:
                parsed_output = json.loads(parsed_output)
                print("DEBUG: Successfully parsed delta tool output as JSON.")
            except json.JSONDecodeError:
                print("DEBUG: Delta tool output is a string but not valid JSON.")
                pass
        elif isinstance(parsed_output, dict):
            print("DEBUG: Delta tool output is already a dictionary.")
        else:
            pass
            print(f"DEBUG: Delta tool output type is {type(parsed_output)}. Wrapping in dict.")
 
        # Reuse saving logic
        print(f"DEBUG: Parsed output before potential wrapping: {parsed_output}") # Print parsed data
        context_data = parsed_output if isinstance(parsed_output, dict) else {'value': parsed_output}
        print(f"DEBUG: Final context_data to be saved: {context_data}") # Print final data for saving
 
        print(f"DEBUG: Preparing to save context. Chat ID: {chat_id}, Source: {source_agent}, Type: {tool_name}, Data: {context_data}") # Use print
        await self.context_service.save_agent_context(
            chat_id=chat_id,
            source_agent=source_agent,
            content_type=tool_name,
            data=context_data
        )
        print(f"DEBUG: Context save attempt complete for tool '{tool_name}' from delta.")

        print(f"--- Handling Tool Result From Delta Complete for Chat {chat_id} ---")