import { useEffect, useRef, useState, useCallback } from 'react';
import { config } from '@/config/environment.config';
import { getAccessToken } from '@/config/storage.config';
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
    // Make this optional again
    setChatListData?: React.Dispatch<React.SetStateAction<PaginatedResponseData<Chat> | null>>;
    setMessageData: React.Dispatch<React.SetStateAction<PaginatedResponseData<Message> | null>>;
    // Optional: Original options can still be passed if needed elsewhere
    options?: WebSocketHookOptions; 
}

const CONNECTION_TIMEOUT = 10000; // 10 seconds timeout for connection

export const useChatWebSocket = ({
    selectedChatId,
    setChatListData,
    setMessageData,
    options 
}: UseChatWebSocketProps) => {
    const ws = useRef<WebSocket | null>(null);
    const [isConnected, setIsConnected] = useState(false);
    const [connectionError, setConnectionError] = useState<Event | string | null>(null); // Allow string for timeout/custom errors
    const [parseError, setParseError] = useState<Error | null>(null);
    const reconnectAttempt = useRef(0);
    const maxReconnectAttempts = 5;
    const isConnecting = useRef(false); // Track connection attempts
    const connectionPromise = useRef<Promise<WebSocket> | null>(null); // Store the pending connection promise


    const [sendingMessage, setSendingMessage] = useState<boolean>(false);
    const [sendMessageError, setSendMessageError] = useState<ApiError | null>(null);

    const handleInternalMessage = useCallback((message: Message) => {
        setMessageData(prevData => {
            if (!prevData || !selectedChatId) return prevData;
            
            let items = prevData.items;
            let foundAndReplacedTemporary = false;

            if (message.sender_type === 'user') {
                const tempIndex = items.findIndex(item => item.sender_type === 'user' && item.isTemporary);
                
                if (tempIndex !== -1) {
                    items = items.map((item, index) => 
                        index === tempIndex ? { ...message, isTemporary: false } : item
                    );
                    foundAndReplacedTemporary = true;
                }
            }

            if (message.sender_type === 'agent' && ['text', 'error', 'tool_use'].includes(message.type)) {
                items = items.filter(item => item.type !== 'thinking');
            }

            if (!foundAndReplacedTemporary) {
                const alreadyExists = items.some(m => m._id === message._id);
                if (!alreadyExists) {
                    const messageToAdd = 
                        message.sender_type === 'agent' && 
                        message.type === 'text' && 
                        message.content === ''
                          ? { ...message, isStreaming: true }
                          : message;
                          
                    items = [messageToAdd, ...items];
                }
            }

            return { ...prevData, items };
        });

        if (setChatListData) {
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
        }

        // Call external handler if provided
        options?.onMessageReceived?.(message);

    }, [selectedChatId, setMessageData, setChatListData, options]);

    const connect = useCallback((): Promise<WebSocket> => {
        // If already connected or connecting, return the existing promise or a resolved one
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
            return Promise.resolve(ws.current);
        }
        if (isConnecting.current && connectionPromise.current) {
            return connectionPromise.current;
        }
        if (!selectedChatId) {
            console.log('[useWebSocket] No chat ID, cannot connect.');
            return Promise.reject('No chat ID selected');
        }

        isConnecting.current = true;
        console.log(`[useWebSocket] Connecting... (Promise created)`);
        setConnectionError(null);
        setParseError(null);

        connectionPromise.current = new Promise(async (resolve, reject) => {
            let timeoutId: NodeJS.Timeout | null = null;

            const cleanup = (socket: WebSocket | null) => {
                if (timeoutId) clearTimeout(timeoutId);
                if (socket) {
                    // Remove listeners to prevent memory leaks on old sockets
                    socket.onopen = null;
                    socket.onmessage = null;
                    socket.onerror = null;
                    socket.onclose = null;
                }
                 if (ws.current === socket) { // Only reset if it's the current socket
                     ws.current = null;
                 }
                isConnecting.current = false;
                connectionPromise.current = null; // Clear the stored promise
            };

            const token = await getAccessToken();
            if (!token) {
                 console.error('[useWebSocket] No auth token found, cannot connect.');
                 setConnectionError('No auth token');
                 cleanup(null);
                 reject(new Error('No auth token'));
                 return;
            }
            const wsBaseUrl = config.API_URL.replace(/^http/, 'ws');
            const wsUrl = `${wsBaseUrl}/chats/ws/${selectedChatId}?token=${encodeURIComponent(token)}`;

            try {
                const currentWs = new WebSocket(wsUrl);
                 // Set a timeout for the connection attempt
                timeoutId = setTimeout(() => {
                    console.error(`[useWebSocket] Connection attempt timed out after ${CONNECTION_TIMEOUT / 1000}s.`);
                    setConnectionError('Connection timed out');
                    setIsConnected(false);
                    cleanup(currentWs); // Pass currentWs for listener removal
                    currentWs.close(1000, "Connection timeout"); // Attempt to close timed-out socket
                    reject(new Error('Connection timed out'));
                }, CONNECTION_TIMEOUT);


                currentWs.onopen = () => {
                    if (timeoutId) clearTimeout(timeoutId); // Clear timeout on successful open
                    console.log(`[useWebSocket] Connected to chat ${selectedChatId}`);
                    ws.current = currentWs; // Set the main ref
                    setIsConnected(true);
                    isConnecting.current = false;
                    connectionPromise.current = null; // Clear the promise on success
                    reconnectAttempt.current = 0;
                    resolve(currentWs); // Resolve the promise with the socket
                };

                currentWs.onmessage = (event) => {
                     // Handle message logic is separate, just keep connection alive
                     // console.log("message received", event.data); // For debugging if needed
                      try {
                        const rawData = event.data;
                        const messageData = JSON.parse(rawData);

                        // --- Handle Different Message Types ---
                        if (messageData.type === "MESSAGE_UPDATE") {
                            // Handle incoming chunk: Find message and append content
                            const { message_id, chunk, is_error } = messageData;
                            setMessageData(prevData => {
                                if (!prevData) return prevData; // Should not happen
                                return {
                                    ...prevData,
                                    items: prevData.items.map(msg =>
                                        msg._id === message_id
                                            ? {
                                                ...msg,
                                                content: msg.content + chunk, // Append chunk
                                                type: is_error ? 'error' : msg.type,
                                            }
                                            : msg
                                    ),
                                };
                            });
                        } else if (messageData.type === "STREAM_END") {
                            // Handle stream end: Find message and mark as not streaming
                            const { message_id } = messageData;
                            setMessageData(prevData => {
                                if (!prevData) return prevData;
                                return {
                                    ...prevData,
                                    items: prevData.items.map(msg =>
                                        msg._id === message_id
                                            ? { ...msg, isStreaming: false }
                                            : msg
                                    ),
                                };
                            });
                        } else {
                            // Assume it's a full MessageData object for chat
                            const validatedMessage: Message = messageData;
                            setParseError(null);
                            handleInternalMessage(validatedMessage);
                        }
                    } catch (error) {
                        console.error('[useWebSocket] Error parsing message or handling update:', error);
                        setParseError(error instanceof Error ? error : new Error('Failed to parse message'));
                    }
                };

                currentWs.onerror = (errorEvent) => {
                    console.error('[useWebSocket] WebSocket Error:', errorEvent);
                    setConnectionError(errorEvent);
                    setIsConnected(false);
                    cleanup(currentWs);
                    reject(errorEvent); // Reject the promise on error
                };

                currentWs.onclose = (closeEvent) => {
                    console.log(`[useWebSocket] Disconnected from chat ${selectedChatId}. Code: ${closeEvent.code}, Reason: ${closeEvent.reason}`);
                    setIsConnected(false);
                    cleanup(currentWs);

                    if (!closeEvent.wasClean) {
                         // Consider if rejecting here is correct, or if it should only happen on initial failure
                        // Rejecting ensures sendChatMessage knows the connection closed unexpectedly
                        reject(closeEvent);
                        // Reconnect logic (can remain outside the promise resolution)
                        if (selectedChatId && reconnectAttempt.current < maxReconnectAttempts) {
                            reconnectAttempt.current++;
                            const delay = Math.pow(2, reconnectAttempt.current) * 1000;
                            console.log(`[useWebSocket] Attempting reconnect ${reconnectAttempt.current}/${maxReconnectAttempts} in ${delay / 1000}s...`);
                            // No need to await here, it's background retry
                            setTimeout(() => connect().catch(err => console.error("Reconnect failed:", err)), delay);
                        }
                    }
                };
            } catch (error) {
                console.error('[useWebSocket] Failed to create WebSocket:', error);
                setConnectionError(error instanceof Event ? error : 'WebSocket creation failed');
                cleanup(null); // Clean up potential partial state
                reject(error); // Reject promise if WebSocket constructor fails
            }
        });

        return connectionPromise.current;

    }, [selectedChatId, handleInternalMessage]); // Dependencies for connect

    const disconnect = useCallback(() => {
        const socketToClose = ws.current; // Capture the current socket
         // Also cancel any pending connection attempt
        if (isConnecting.current && connectionPromise.current) {
            console.log('[useWebSocket] Disconnecting: Cancelling pending connection attempt.');
             // Rejecting might be complex if the promise is already settled.
             // Instead, rely on the socket close triggering cleanup.
            connectionPromise.current = null; // Clear the reference
            isConnecting.current = false;
        }

        if (socketToClose) {
            console.log('[useWebSocket] Closing WebSocket connection explicitly.');
            socketToClose.close(1000, 'Client disconnecting');
            // Cleanup happens in onclose handler
        } else {
            console.log('[useWebSocket] disconnect called, but no active socket.');
        }
        // Reset state immediately for UI responsiveness
        setIsConnected(false);
        setConnectionError(null);
        setParseError(null);
        reconnectAttempt.current = 0; // Reset reconnect attempts on explicit disconnect
    }, []); // Dependencies for disconnect

    // --- Effect for managing connection based on selectedChatId ---
    useEffect(() => {
        if (selectedChatId) {
            // Don't auto-connect here if we want sendChatMessage to trigger it
            // connect().catch(err => console.error("Initial connection failed:", err));
            console.log(`[useWebSocket Effect] Chat selected: ${selectedChatId}. Ready to connect on demand.`);
        } else {
            disconnect(); // Disconnect if no chat is selected
        }

        // Cleanup function on component unmount or selectedChatId change
        return () => {
            disconnect();
        };
    }, [selectedChatId, disconnect]); // Removed 'connect' dependency


    const sendChatMessage = useCallback(async (payload: CreateMessagePayload): Promise<{ success: boolean; error?: string }> => {
        setSendingMessage(true);
        setSendMessageError(null);
        
        let currentWs = ws.current;

        try {
            // 1. Check if connected
            if (!currentWs || currentWs.readyState !== WebSocket.OPEN) {
                console.log(`[sendChatMessage] WebSocket not open (State: ${currentWs?.readyState}). Attempting to connect...`);
                
                 if (isConnecting.current) {
                    console.warn(`[sendChatMessage] Connection already in progress. Waiting for existing attempt...`);
                    // Wait for the ongoing connection attempt
                    if (!connectionPromise.current) {
                        // Should not happen if isConnecting is true, but handle defensively
                        throw new Error("Connection in progress but no promise found.");
                    }
                     try {
                        currentWs = await connectionPromise.current; // Await the stored promise
                        console.log(`[sendChatMessage] Ongoing connection successful.`);
                     } catch (connectError) {
                         console.error(`[sendChatMessage] Ongoing connection attempt failed:`, connectError);
                         const errorMsg = connectError instanceof Error ? connectError.message : String(connectError);
                         setSendMessageError({ message: `Connection attempt failed: ${errorMsg}`, error_code: 'WS_CONNECT_FAIL', status_code: 0 });
                         return { success: false, error: 'WS_CONNECT_FAIL' };
                     }

                 } else {
                    // Attempt a new connection
                    try {
                        currentWs = await connect(); // connect now returns a promise
                        console.log(`[sendChatMessage] Connection successful.`);
                        // ws.current should be set by connect's onopen handler
                    } catch (connectError) {
                        console.error(`[sendChatMessage] Failed to connect before sending:`, connectError);
                         const errorMsg = connectError instanceof Error ? connectError.message : String(connectError);
                        setSendMessageError({ message: `Failed to connect: ${errorMsg}`, error_code: 'WS_CONNECT_FAIL', status_code: 0 });
                        return { success: false, error: 'WS_CONNECT_FAIL' };
                    }
                }
            }

            // 2. Send message if connected
            if (currentWs && currentWs.readyState === WebSocket.OPEN) {
                currentWs.send(JSON.stringify(payload));
                console.log("[sendChatMessage] Message sent successfully.");
                return { success: true };
            } else {
                 // This case should ideally be caught by the connection logic errors above
                console.error("[sendChatMessage] WebSocket is not open after connection attempt.");
                setSendMessageError({ message: 'WebSocket connection failed unexpectedly.', error_code: 'WS_UNEXPECTED_STATE', status_code: 0 });
                return { success: false, error: 'WS_UNEXPECTED_STATE' };
            }

        } catch (error) {
            console.error("Error sending message via WebSocket:", error);
            const apiError: ApiError = { message: 'Failed to send message', error_code: 'WS_SEND_ERROR', status_code: 0 };
            setSendMessageError(apiError);
            return { success: false, error: 'WS_SEND_ERROR' };
        } finally {
            setSendingMessage(false);
        }
    }, [connect]); // Dependency on the new connect function

    return {
        ws, // Note: ws.current might be null initially or after disconnect
        isConnected,
        connectionError,
        parseError,
        sendChatMessage, 
        sendingMessage,
        sendMessageError,
    };
}; 