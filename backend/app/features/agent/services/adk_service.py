import traceback
from typing import TYPE_CHECKING, Optional, Tuple, Any, AsyncGenerator, Dict
from beanie import PydanticObjectId
from google.adk.runners import Runner
from google.adk.events import Event
from google.genai import types as genai_types
import json
import logging

# Import the specific agent instance directly
from app.agents.jonas_agent import jonas_agent

# Assuming ContextService is in a 'context' feature - CORRECTING this assumption
from app.features.chat.services import ContextService

if TYPE_CHECKING:
    # from .agent_service import AgentOutputEvent # Old import
    from .schemas import AgentOutputEvent, AgentOutputType # Import from schemas
    from app.features.chat.models import Chat, Message
    from app.features.chat.services import ChatService, WebSocketService
    from app.features.agent.repositories.adk_repository import ADKRepository

logger = logging.getLogger(__name__)

class ADKService:
    """Service layer for handling ADK agent interactions via the Runner."""

    def __init__(
        self,
        adk_repository: "ADKRepository",
        # Services needed by handlers and state preparation
        chat_service: "ChatService",
        context_service: "ContextService",
        app_name: str = "Jonas" # Match ADKRepository
    ):
        self.adk_repo = adk_repository
        self.chat_service = chat_service
        self.context_service = context_service
        self.app_name = app_name
        # Runner is initialized per-request or per-agent in the processing method
        # self.runner = None # Initialize runner later
        logger.info("ADKService initialized.")

    # --- Add State Preparation Method --- #
    async def _prepare_initial_state(
        self,
        chat: "Chat",
        user_id_str: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Prepares the initial state dictionary for a new session, including context."""
        initial_state = {
            "invocation_user_id": user_id_str,
            "invocation_session_id": session_id
            # Add other base state required by agents if any
        }

        # Fetch and format context items using the injected context_service
        context_items = await self.context_service.fetch_all_chat_context(chat.id)
        logger.debug(f"ADKService: Fetched {len(context_items)} context items for chat {chat.id}.")
        formatted_context_state = {'context': {}}
        for item in context_items:
            if item.source_agent not in formatted_context_state['context']:
                formatted_context_state['context'][item.source_agent] = {}
            formatted_context_state['context'][item.source_agent][item.content_type] = item.data

        # Merge formatted context into the initial state
        initial_state.update(formatted_context_state)
        context_key_count = sum(len(types) for types in formatted_context_state.get('context', {}).values())
        logger.debug(f"ADKService: Prepared initial state with {context_key_count} context items.")
        return initial_state

    async def run_agent_turn(
        self,
        chat: "Chat",
        user_id: PydanticObjectId,
        user_content: str,
    ) -> AsyncGenerator["AgentOutputEvent", None]: # Yield events back to caller
        """
        Processes a user message using the jonas_agent via the ADK Runner
        and yields structured events representing the agent's output.
        """
        agent_message_id: Optional[PydanticObjectId] = None
        accumulated_content = ""
        session_id = str(chat.id)
        chat_id_obj = chat.id
        user_id_str = str(user_id)
        should_break_loop = False

        # Get session service from repo
        session_service = self.adk_repo.get_session_service()

        # Initialize Runner for this agent and request
        runner = Runner(
            agent=jonas_agent,
            app_name=self.app_name,
            session_service=session_service
        )
        logger.info(f"ADK Runner initialized for agent '{jonas_agent.name}' in session {session_id}")

        try:
            # --- Session Management --- #
            # Check if session exists before potentially preparing state
            session_obj = session_service.get_session(
                 app_name=self.app_name, user_id=user_id_str, session_id=session_id
            )
            initial_state_for_creation: Optional[Dict[str, Any]] = None
            if session_obj is None:
                logger.debug(f"Session {session_id} not found, preparing initial state.")
                initial_state_for_creation = await self._prepare_initial_state(chat, user_id_str, session_id)

            # Load or create session, passing initial state only if creating
            await self.adk_repo.load_or_create_session(
                 chat=chat,
                 user_id=user_id,
                 initial_state=initial_state_for_creation # Pass prepared state
            )
            logger.debug(f"Session loaded/created for chat {chat_id_obj}")
            # --- End Session Management ---

            # --- Prepare User Message --- 
            content = genai_types.Content(role='user', parts=[genai_types.Part(text=user_content)])
            logger.debug(f"Prepared user message for ADK: {content}")
            # --- End Prepare User Message ---

            # --- ADK Runner Event Loop --- 
            logger.info(f"Starting ADK Runner loop for session {session_id}...")
            async for event in runner.run_async(user_id=user_id_str, session_id=session_id, new_message=content):
                logger.debug(f"ADK Event Received: Type={type(event).__name__}, Author={event.author}, Partial={event.partial}, Final={event.is_final_response()}, Actions={event.actions}, Error={event.error_code}")

                # --- Event Processing Logic --- 
                # Import late to avoid circularity if AgentService needed them
                # Now import directly from schemas (one level up)
                from ..schemas import AgentOutputEvent, AgentOutputType

                function_responses = event.get_function_responses()
                tool_results_in_delta = event.actions.state_delta.get('tool_result')

                output_event: Optional[AgentOutputEvent] = None

                if event.partial and event.content and event.content.parts and event.content.parts[0].text:
                    agent_message_id, accumulated_content, output_event = await self._handle_streaming_chunk(
                        event, chat, session_id, agent_message_id, accumulated_content
                    )
                elif event.actions and event.actions.transfer_to_agent:
                    output_event = await self._handle_delegation_signal(event, chat)
                elif event.get_function_calls():
                    # Log tool call requests, but don't yield an event unless needed by UI
                    self._log_tool_call_request(event)
                elif function_responses:
                    logger.debug("Processing tool result via get_function_responses()")
                    await self._handle_tool_result(event, chat_id_obj)
                    # TODO: Decide if tool results should yield an AgentOutputEvent
                elif tool_results_in_delta:
                    logger.debug("Processing tool result via state_delta['tool_result']")
                    await self._handle_tool_result_from_delta(tool_results_in_delta, event.author, chat_id_obj)
                    # TODO: Decide if tool results should yield an AgentOutputEvent
                elif event.is_final_response():
                    accumulated_content, should_break_loop, output_event = await self._handle_final_response(
                        event, chat, session_id, agent_message_id, accumulated_content
                    )
                elif event.error_code or event.error_message:
                    output_event = await self._handle_error_event(event, chat, session_id)
                    should_break_loop = True # Stop processing on error

                # Yield the processed event if one was generated
                if output_event:
                    yield output_event
                # --- End Event Processing --- 

                if should_break_loop:
                    logger.info(f"Breaking ADK Runner loop for session {session_id}.")
                    break
            # --- End ADK Runner Event Loop --- 
            logger.info(f"ADK Runner loop finished for session {session_id}.")

        except Exception as e:
            logger.error(f"ADKService: Error during Runner execution for session {session_id}: {e}", exc_info=True)
            traceback.print_exc()
            # Yield a final error event
            # Import late (one level up)
            from ..schemas import AgentOutputEvent, AgentOutputType # Import from schemas
            error_content = "An internal error occurred while processing your request with the agent."
            # We might not have `chat` here if the error was very early
            if chat:
                 error_msg = await self.chat_service._create_and_broadcast_message(
                     chat=chat,
                     sender_type='agent',
                     content=error_content,
                     message_type='error',
                 )
                 yield AgentOutputEvent(
                     type=AgentOutputType.ERROR,
                     content=error_content,
                     message_id=error_msg.id if error_msg else None
                 )
            else:
                 yield AgentOutputEvent(
                     type=AgentOutputType.ERROR,
                     content=error_content
                 )
        finally:
            logger.debug(f"ADKService turn completed for session {session_id}.")
            # No specific cleanup needed for InMemorySessionService typically

    async def _handle_streaming_chunk(
        self,
        event: Event,
        chat: "Chat",
        session_id: str,
        agent_message_id: Optional[PydanticObjectId],
        accumulated_content: str
    ) -> Tuple[Optional[PydanticObjectId], str, "AgentOutputEvent"]:
        """Handles a streaming text chunk event, creates/updates DB message, yields chunk event."""
        # Import late (one level up)
        from ..schemas import AgentOutputEvent, AgentOutputType # Import from schemas
        chunk = event.content.parts[0].text
        accumulated_content += chunk
        new_agent_message_id = agent_message_id
        output_event: Optional[AgentOutputEvent] = None

        if agent_message_id is None: # Create DB message on first chunk
            logger.debug(f"First chunk received for session {session_id}. Creating agent message.")
            agent_msg_model: Optional["Message"] = await self.chat_service._create_and_broadcast_message(
                chat=chat,
                sender_type='agent',
                content="", # Start empty, will be updated by caller later
                message_type='text',
            )
            if agent_msg_model:
                new_agent_message_id = agent_msg_model.id
                logger.info(f"Created agent message {new_agent_message_id} for stream in chat {chat.id}")
                # Yield event *after* creating the message ID
                output_event = AgentOutputEvent(
                    type=AgentOutputType.STREAM_START,
                    message_id=new_agent_message_id,
                    content=chunk # Include first chunk here
                )
            else:
                logger.error(f"Failed to create initial agent message DB entry for chat {chat.id}")
                # Cannot yield a STREAM_START without a message_id
                # Yield an error instead?
                output_event = AgentOutputEvent(type=AgentOutputType.ERROR, content="Failed to initialize agent message.")
                # Or just log and potentially fail later?
        else:
            # Subsequent chunk, just yield the chunk data
            output_event = AgentOutputEvent(
                type=AgentOutputType.STREAM_CHUNK,
                message_id=new_agent_message_id,
                content=chunk
            )

        # Note: Broadcasting the chunk via websocket is now handled by the caller (e.g., WebSocketController)
        # based on the yielded AgentOutputEvent.

        return new_agent_message_id, accumulated_content, output_event

    async def _handle_delegation_signal(self, event: Event, chat: "Chat") -> "AgentOutputEvent":
        """Handles a delegation signal event, creates DB message, yields delegation event."""
        # Import late (one level up)
        from ..schemas import AgentOutputEvent, AgentOutputType # Import from schemas
        delegated_agent = event.actions.transfer_to_agent
        logger.info(f"Detected delegation to {delegated_agent} in chat {chat.id}. Creating action message.")
        content = f"Delegating to {delegated_agent}..."
        # Create an action message in the chat log
        action_msg = await self.chat_service._create_and_broadcast_message(
            chat=chat,
            sender_type='agent',
            content=content,
            message_type='action',
            tool_name=delegated_agent # Store agent name in tool_name field for actions
        )
        return AgentOutputEvent(
            type=AgentOutputType.DELEGATION,
            content=content,
            message_id=action_msg.id if action_msg else None,
            tool_name=delegated_agent
        )

    def _log_tool_call_request(self, event: Event):
        """Handles a tool call request event (logging only)."""
        function_calls = event.get_function_calls()
        for call in function_calls:
            # Avoid logging the delegation function call itself as a "tool use"
            if call.name != 'transfer_to_agent':
                logger.info(f"Agent '{event.author}' requested tool '{call.name}' (handled by Runner). Args: {call.args}")

    async def _handle_tool_result(self, event: Event, chat_id: PydanticObjectId):
        """Handles a tool result event by logging it and saving each function response as context."""
        function_responses = event.get_function_responses()
        source_agent = event.author

        logger.debug(f"--- Handling Tool Result for Chat {chat_id} (via get_function_responses) ---")
        logger.debug(f"Raw Event Object: {event}")
        for resp in function_responses:
            logger.debug(f"Processing result for tool '{resp.name}' from '{source_agent}'. Raw Response: {resp.response}")
            await self._save_tool_response_as_context(chat_id, source_agent, resp.name, resp.response)
        logger.debug(f"--- Handling Tool Result Complete for Chat {chat_id} ---")

    async def _handle_tool_result_from_delta(self, tool_result_data: Any, source_agent: str, chat_id: PydanticObjectId):
        """Handles tool results found in the event's state delta."""
        logger.debug(f"--- Handling Tool Result From Delta for Chat {chat_id} ---")
        # Limitation: tool name might not be explicitly in the delta.
        # Inferring based on agent or data structure might be needed.
        # Example: If source_agent is 'database_agent', assume 'query_sql_database'?
        tool_name = "unknown_tool_from_delta"
        if source_agent == "database_agent" and isinstance(tool_result_data, dict) and 'result' in tool_result_data:
             tool_name = "query_sql_database" # Heuristic guess

        logger.debug(f"Processing delta result potentially for tool '{tool_name}' from '{source_agent}'. Raw Data: {tool_result_data}")
        await self._save_tool_response_as_context(chat_id, source_agent, tool_name, tool_result_data)
        logger.debug(f"--- Handling Tool Result From Delta Complete for Chat {chat_id} ---")

    async def _save_tool_response_as_context(
        self,
        chat_id: PydanticObjectId,
        source_agent: str,
        tool_name: str,
        raw_response: Any
    ):
        """Extracts, parses, and saves a tool response to the context service."""
        actual_tool_output = None
        if isinstance(raw_response, dict) and 'status' in raw_response and 'data' in raw_response:
            actual_tool_output = raw_response.get('data')
        elif isinstance(raw_response, dict) and 'status' in raw_response and 'result' in raw_response: # Handle db agent case
            actual_tool_output = raw_response.get('result')
        elif isinstance(raw_response, dict):
            actual_tool_output = raw_response.get('result')
            if actual_tool_output is None:
                 actual_tool_output = raw_response # Use the whole dict if no 'result'
        else:
            actual_tool_output = raw_response
        logger.debug(f"Extracted actual tool output: {actual_tool_output}")

        # --- Parsing Logic --- 
        parsed_output = actual_tool_output
        if isinstance(parsed_output, str):
            try:
                parsed_output = json.loads(parsed_output)
                logger.debug("Successfully parsed tool output as JSON.")
            except json.JSONDecodeError:
                logger.debug("Tool output is a string but not valid JSON.")
                pass # Leave as string
        elif isinstance(parsed_output, dict):
           logger.debug("Tool output is already a dictionary.")
        else:
           logger.debug(f"Tool output type is {type(parsed_output)}, will be wrapped in dict.")

        # --- Context Saving Logic --- 
        logger.debug(f"Parsed output before context wrapping: {parsed_output}")
        context_data = parsed_output if isinstance(parsed_output, dict) else {'value': parsed_output}
        logger.debug(f"Final context_data to be saved: {context_data}")

        try:
            logger.debug(f"Calling context_service.save_agent_context for chat {chat_id}, agent {source_agent}, type {tool_name}")
            await self.context_service.save_agent_context(
                chat_id=chat_id,
                source_agent=source_agent,
                content_type=tool_name,
                data=context_data
            )
            logger.debug(f"Context save attempt complete for tool '{tool_name}'.")
        except Exception as e:
            logger.error(f"Failed to save context for tool '{tool_name}' in chat {chat_id}: {e}", exc_info=True)

    async def _handle_final_response(
        self,
        event: Event,
        chat: "Chat",
        session_id: str,
        agent_message_id: Optional[PydanticObjectId],
        accumulated_content: str
    ) -> Tuple[str, bool, Optional["AgentOutputEvent"]]:
        """Handles the final response event, updates DB message, yields final event."""
        # Import late (one level up)
        from ..schemas import AgentOutputEvent, AgentOutputType # Import from schemas
        logger.info(f"Final response event received for session {session_id} from author {event.author}.")
        logger.debug(f"Final response event details: {event}")
        final_text = None
        final_content_for_db = accumulated_content # Start with accumulated stream content
        output_event: Optional[AgentOutputEvent] = None
        should_break = True # Assume we break unless it's an ignored final response

        # --- Extract Final Text --- 
        if event.content and event.content.parts and event.content.parts[0].text:
            final_text = event.content.parts[0].text
            if agent_message_id and not event.partial: # Part of stream, append final chunk
                final_content_for_db += final_text
            elif not agent_message_id: # Whole message is in this final event (no stream prior)
                final_content_for_db = final_text

        # --- Handle Agent-Specific Final Response Logic --- 
        # Example: Ignore final response text from database_agent
        if event.author == 'database_agent':
            logger.debug("Ignoring final response text from database_agent as per logic.")
            final_content_for_db = accumulated_content # Use only streamed content if any
            # Don't yield a FINAL_MESSAGE event for the DB agent's ignored output
            # If there was a stream (unlikely for DB agent), we still need to signal its end
            if agent_message_id:
                 output_event = AgentOutputEvent(
                     type=AgentOutputType.STREAM_END,
                     message_id=agent_message_id
                 )
            # We *do* want to break the loop as the DB agent's turn is done.
        else:
            # --- Handle Normal Final Response --- 
            if agent_message_id:
                # This was the end of a stream
                logger.debug(f"Final chunk received for stream message {agent_message_id}. Total length: {len(final_content_for_db)}")
                output_event = AgentOutputEvent(
                    type=AgentOutputType.STREAM_END,
                    message_id=agent_message_id,
                    content=final_text # Include the final chunk text if any
                )
                # Update the full message content in DB
                if final_content_for_db:
                    await self.chat_service.update_message_content(agent_message_id, final_content_for_db)
                    logger.info(f"Updated final content for message {agent_message_id}")
                else:
                    logger.warning(f"Final response for streamed message {agent_message_id} had no text content to update.")

            elif final_content_for_db: # Final response is the only content (no stream)
                logger.info(f"Final response is the only content. Creating single message.")
                # Create the single message in DB
                final_msg = await self.chat_service._create_and_broadcast_message(
                    chat=chat,
                    sender_type='agent',
                    content=final_content_for_db,
                    message_type='text',
                )
                if final_msg:
                     output_event = AgentOutputEvent(
                         type=AgentOutputType.FINAL_MESSAGE,
                         message_id=final_msg.id,
                         content=final_content_for_db
                     )
                else:
                     logger.error(f"Failed to create final message for chat {chat.id}")
                     output_event = AgentOutputEvent(type=AgentOutputType.ERROR, content="Failed to save final agent message.")

            else:
                # Final response event had no text content and no prior stream. Maybe just state changes?
                logger.warning(f"Final response event from {event.author} had no text content and no prior stream. No message generated.")
                # No output event needed unless we want to signal completion explicitly

        return final_content_for_db, should_break, output_event

    async def _handle_error_event(self, event: Event, chat: "Chat", session_id: str) -> "AgentOutputEvent":
        """Handles an explicit error event from the ADK runner, yields error event."""
        # Import late (one level up)
        from ..schemas import AgentOutputEvent, AgentOutputType # Import from schemas
        error_msg_content = f"Agent Error ({event.error_code}): {event.error_message}" if event.error_message else "An unspecified agent error occurred."
        logger.error(f"ADK Runner Error Event in session {session_id}: {error_msg_content}")

        # Create error message in DB
        error_msg = await self.chat_service._create_and_broadcast_message(
            chat=chat,
            sender_type='agent',
            content=error_msg_content,
            message_type='error'
        )
        return AgentOutputEvent(
            type=AgentOutputType.ERROR,
            content=error_msg_content,
            message_id=error_msg.id if error_msg else None
        ) 