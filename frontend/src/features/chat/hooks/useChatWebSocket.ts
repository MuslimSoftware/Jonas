import { useState, useEffect, useCallback, useMemo } from 'react';
import { useWebSocket, WebSocketOptions } from '@/api/useWebSocket';
import { Message, CreateMessagePayload } from '@/api/types/chat.types';
import { config } from '@/config/environment.config';
import { getAccessToken } from '@/config/storage.config';

export interface UseChatWebSocketOptions {
  onMessageReceived?: (message: Message) => void;
  // Add other chat-specific callbacks if needed
}

export const useChatWebSocket = (chatId: string | null, options: UseChatWebSocketOptions = {}) => {
  const { onMessageReceived } = options;
  const [wsUrl, setWsUrl] = useState<string | null>(null);
  const [lastParsedMessage, setLastParsedMessage] = useState<Message | null>(null);
  const [parseError, setParseError] = useState<Error | null>(null);

  const wsBaseUrl = useMemo(() => config.API_URL.replace(/^http/, 'ws'), []);

  // Effect to construct the WebSocket URL with auth token
  useEffect(() => {
    let isMounted = true;
    const constructUrl = async () => {
      if (!chatId) {
        setWsUrl(null);
        return;
      }
      const token = await getAccessToken();
      if (!token) {
        console.error('[useChatWebSocket] No auth token found, cannot connect.');
        setWsUrl(null);
        return;
      }
      const url = `${wsBaseUrl}/chats/ws/${chatId}?token=${encodeURIComponent(token)}`;
      if (isMounted) {
        setWsUrl(url);
      }
    };

    constructUrl();

    return () => {
      isMounted = false;
    };
  }, [chatId, wsBaseUrl]);

  // Callback for handling raw messages from the generic hook
  const handleRawMessage = useCallback((event: MessageEvent) => {
    try {
      const parsedMessage: Message = JSON.parse(event.data);
      setLastParsedMessage(parsedMessage);
      setParseError(null);
      onMessageReceived?.(parsedMessage); // Call external callback
    } catch (error) {
      console.error('[useChatWebSocket] Error parsing message:', error);
      setParseError(error instanceof Error ? error : new Error('Failed to parse message'));
      setLastParsedMessage(null);
    }
  }, [onMessageReceived]);

  // Configure options for the generic useWebSocket hook
  const wsOptions: WebSocketOptions = useMemo(() => ({
    onMessage: handleRawMessage,
    // Pass through other generic options if needed (onOpen, onClose, onError)
  }), [handleRawMessage]);

  // Use the generic WebSocket hook
  const {
    isConnected,
    error: connectionError,
    sendMessage: sendRawMessage,
    connect,
    disconnect,
  } = useWebSocket(wsUrl, wsOptions);

  // Typed send function for chat messages
  const sendChatMessage = useCallback((payload: CreateMessagePayload) => {
    try {
      const messageString = JSON.stringify(payload);
      sendRawMessage(messageString);
    } catch (error) {
      console.error('[useChatWebSocket] Error stringifying message:', error);
      // Handle stringification error (e.g., set an error state)
    }
  }, [sendRawMessage]);

  return {
    isConnected,
    lastReceivedMessage: lastParsedMessage,
    connectionError, // Error from the WebSocket connection itself
    parseError,      // Error specifically from parsing messages
    sendChatMessage,
    connect,         // Expose connect/disconnect for potential manual control
    disconnect,
  };
}; 