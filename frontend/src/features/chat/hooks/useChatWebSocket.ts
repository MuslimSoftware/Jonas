import { useEffect, useRef, useState, useCallback } from 'react';
import { config } from '@/config/environment.config'; // Import config
import { getAccessToken } from '@/config/storage.config'; // Import token getter
import { 
  Message, 
  CreateMessagePayload, 
  PaginatedResponseData, 
  Chat 
} from '@/api/types/chat.types';
import { ApiError } from '@/api/types/api.types';

interface WebSocketHookOptions {
  onMessageReceived?: (message: Message) => void; // Keep original option if needed externally
}

interface UseChatWebSocketProps {
    selectedChatId: string | null;
    // Add state setters from context
    setChatListData: React.Dispatch<React.SetStateAction<PaginatedResponseData<Chat> | null>>;
    setMessageData: React.Dispatch<React.SetStateAction<PaginatedResponseData<Message> | null>>;
    // Optional: Original options can still be passed if needed elsewhere
    options?: WebSocketHookOptions; 
}

export const useChatWebSocket = ({
    selectedChatId,
    setChatListData,
    setMessageData,
    options 
}: UseChatWebSocketProps) => {
    const ws = useRef<WebSocket | null>(null);
    const [isConnected, setIsConnected] = useState(false);
    const [connectionError, setConnectionError] = useState<Event | null>(null);
    const [parseError, setParseError] = useState<Error | null>(null);
    const reconnectAttempt = useRef(0);
    const maxReconnectAttempts = 5;

    // State for sending messages (moved from Manager)
    const [sendingMessage, setSendingMessage] = useState<boolean>(false);
    const [sendMessageError, setSendMessageError] = useState<ApiError | null>(null);

    // Internal handler that updates context state (moved from Manager)
    const handleInternalMessage = useCallback((message: Message) => {
        // Update messageData
        setMessageData(prevData => {
            if (!prevData || !selectedChatId) return prevData; // Check against current selectedChatId
            const alreadyExists = prevData.items.some(m => m._id === message._id);
            if (alreadyExists) return prevData;
            return { ...prevData, items: [message, ...prevData.items] };
        });

        // Update chatListData
        setChatListData(prevData => {
            if (!prevData || !selectedChatId) return prevData;
            const chatIndex = prevData.items.findIndex(chat => chat._id === selectedChatId);
            if (chatIndex === -1) return prevData;

            const chatToUpdate = prevData.items[chatIndex];
            const currentLatestStr = chatToUpdate.latest_message_timestamp;
            const newMsgStr = message.created_at;
            const correctedCurrentLatestStr = currentLatestStr && !currentLatestStr.endsWith('Z') ? `${currentLatestStr}Z` : currentLatestStr;
            const correctedNewMsgStr = newMsgStr && !newMsgStr.endsWith('Z') ? `${newMsgStr}Z` : newMsgStr;
            const currentLatestTimestampValue = correctedCurrentLatestStr ? new Date(correctedCurrentLatestStr).getTime() : 0;
            const newMessageTimestampValue = correctedNewMsgStr ? new Date(correctedNewMsgStr).getTime() : 0;

            if (!newMessageTimestampValue || (currentLatestTimestampValue && newMessageTimestampValue < currentLatestTimestampValue)) {
                return prevData;
            }

            const updatedChat = {
                ...chatToUpdate,
                latest_message_content: message.content,
                latest_message_timestamp: message.created_at,
                updated_at: message.created_at
            };
            const newItems = prevData.items.filter(chat => chat._id !== selectedChatId);
            newItems.unshift(updatedChat);
            return { ...prevData, items: newItems };
        });

        // Call external handler if provided
        options?.onMessageReceived?.(message);

    }, [selectedChatId, setMessageData, setChatListData, options]);

    const connect = useCallback(async () => {
        if (!selectedChatId) {
            console.log('[useWebSocket] No chat ID, skipping connection.');
            return;
        }
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
            console.log('[useWebSocket] Already connected.');
            return;
        }

        // Construct URL manually
        const token = await getAccessToken();
        if (!token) {
             console.error('[useWebSocket] No auth token found, cannot connect.');
             setConnectionError(new Event('No auth token')); // Set an error state
             return;
        }
        const wsBaseUrl = config.API_URL.replace(/^http/, 'ws');
        // Construct path relative to the base API URL (which includes /api/v1)
        const wsUrl = `${wsBaseUrl}/chats/ws/${selectedChatId}?token=${encodeURIComponent(token)}`; 

        console.log(`[useWebSocket] Connecting...`);
        setConnectionError(null);
        setParseError(null);

        try {
            // Store the specific instance being created
            const currentWs = new WebSocket(wsUrl);
            ws.current = currentWs; // Assign immediately

            currentWs.onopen = () => {
                // Check if the socket that opened is still the current one
                if (ws.current === currentWs) {
                    console.log(`[useWebSocket] Connected to chat ${selectedChatId}`);
                    setIsConnected(true);
                    reconnectAttempt.current = 0; // Reset reconnect attempts on successful connection
                } else {
                    // This log helps confirm if an old socket's onopen fired late
                    console.log(`[useWebSocket] onopen triggered for a stale socket instance (chat ${selectedChatId}), ignoring.`);
                    // Optionally close this potentially orphaned socket if it wasn't closed properly
                    currentWs.close(1006, "Stale socket detected"); 
                }
            };

            currentWs.onmessage = (event) => {
                try {
                    const messageData = JSON.parse(event.data);
                    // TODO: Add validation here using a Pydantic-like schema validator if possible
                    const validatedMessage: Message = messageData; // Assume validation for now
                    setParseError(null); // Clear previous parse errors
                    handleInternalMessage(validatedMessage); // Use internal handler
                } catch (error) {
                    console.error('[useWebSocket] Error parsing message:', error);
                    setParseError(error instanceof Error ? error : new Error('Failed to parse message'));
                }
            };

            currentWs.onerror = (errorEvent) => {
                // Check if the socket that errored is still the current one
                if (ws.current === currentWs) {
                    console.error('[useWebSocket] WebSocket Error:', errorEvent); // Existing log
                    console.log('[useWebSocket] onerror: Setting isConnected to false.'); // Add log
                    setConnectionError(errorEvent);
                    setIsConnected(false); // Ensure connection status is false on error
                } else {
                    console.log(`[useWebSocket] onerror triggered for a stale socket instance (chat ${selectedChatId}), ignoring.`);
                }
            };

            currentWs.onclose = (closeEvent) => {
                 // Check if the socket that closed is still the current one
                if (ws.current === currentWs) {
                    console.log(`[useWebSocket] Disconnected from chat ${selectedChatId}. Code: ${closeEvent.code}, Reason: ${closeEvent.reason}`); // Existing log
                    console.log('[useWebSocket] onclose: Setting isConnected to false.'); // Add log
                    setIsConnected(false);
                    // Only nullify the ref if it's the *current* socket closing.
                    // The disconnect function also handles this, but belt-and-suspenders.
                    if (ws.current === currentWs) {
                         ws.current = null;
                    }
                    // Basic Reconnect logic (only if not closed cleanly or by selection change)
                    if (selectedChatId && !closeEvent.wasClean && reconnectAttempt.current < maxReconnectAttempts) {
                        reconnectAttempt.current++;
                        const delay = Math.pow(2, reconnectAttempt.current) * 1000; // Exponential backoff
                        console.log(`[useWebSocket] Attempting reconnect ${reconnectAttempt.current}/${maxReconnectAttempts} in ${delay / 1000}s...`);
                        setTimeout(connect, delay);
                    }
                } else {
                     console.log(`[useWebSocket] onclose triggered for a stale socket instance (chat ${selectedChatId}), ignoring.`);
                }
            };
        } catch (error) {
            console.error('[useWebSocket] Failed to create WebSocket:', error);
            setConnectionError(error instanceof Event ? error : new Event('WebSocket creation failed'));
        }

    }, [selectedChatId, handleInternalMessage]);

    const disconnect = useCallback(() => {
        const socketToClose = ws.current; // Capture the current socket
        if (socketToClose) {
            console.log('[useWebSocket] Closing WebSocket connection explicitly.');
            // Check if this socket is already closing/closed? Might not be needed.
            socketToClose.close(1000, 'Client disconnecting');
            // Only nullify if it's the same socket we intended to close
            if (ws.current === socketToClose) {
                ws.current = null;
            }
            setIsConnected(false); // Set state regardless
            setConnectionError(null);
            setParseError(null);
            reconnectAttempt.current = 0; // Reset reconnect attempts on explicit disconnect
        } else {
            // Add a log here for when disconnect is called but there's no socket
            console.log('[useWebSocket] disconnect called, but no active socket (ws.current is null).');
        }
    }, []);

    useEffect(() => {
        if (selectedChatId) {
            connect();
        } else {
            disconnect(); // Disconnect if no chat is selected
        }

        // Cleanup function to disconnect when component unmounts or selectedChatId changes
        return () => {
            disconnect();
        };
    }, [selectedChatId, connect, disconnect]);

    // Modified sendChatMessage (moved from Manager)
    const sendChatMessage = useCallback(async (payload: CreateMessagePayload): Promise<{ success: boolean; error?: string }> => {
        // Log the state just before the check
        console.log(`[sendChatMessage] Check: isConnected=${isConnected}, ws.current=${ws.current}, readyState=${ws.current?.readyState}`);

        // Primary check: is the CURRENT ref pointing to an OPEN socket?
        if (!ws.current || ws.current.readyState !== WebSocket.OPEN) {
            console.warn(`[sendChatMessage] WebSocket ref not current or not open. Cannot send. isConnected state: ${isConnected}`);
            const error: ApiError = { message: 'WebSocket not ready', error_code: 'WS_NOT_READY', status_code: 0 };
            setSendMessageError(error);
            return { success: false, error: 'WS_NOT_READY' };
        }
        //

        // We passed the primary check, proceed.
        setSendingMessage(true);
        setSendMessageError(null);
        try {
            ws.current.send(JSON.stringify(payload));
            setSendingMessage(false);
            return { success: true };
        } catch (error) {
            console.error("Error sending message via WebSocket:", error);
            const apiError: ApiError = { message: 'Failed to send message', error_code: 'WS_SEND_ERROR', status_code: 0 };
            setSendMessageError(apiError);
            setSendingMessage(false);
            return { success: false, error: 'WS_SEND_ERROR' };
        }
    }, []);

    return {
        ws,
        isConnected,
        connectionError,
        parseError,
        sendChatMessage, // Return the modified send function
        // Return sending state
        sendingMessage,
        sendMessageError,
    };
}; 