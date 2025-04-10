import { useState, useEffect, useRef, useCallback } from 'react';

export interface WebSocketOptions {
  onOpen?: (event: Event) => void;
  onMessage?: (event: MessageEvent) => void;
  onError?: (event: Event) => void;
  onClose?: (event: CloseEvent) => void;
  reconnectLimit?: number; // Optional: Add reconnect logic later
  reconnectInterval?: number; // Optional: Add reconnect logic later
}

export interface WebSocketState {
  isConnected: boolean;
  lastMessage: MessageEvent | null;
  error: Event | null;
}

export const useWebSocket = (url: string | null, options: WebSocketOptions = {}) => {
  const { onOpen, onMessage, onError, onClose } = options;
  const ws = useRef<WebSocket | null>(null);
  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    lastMessage: null,
    error: null,
  });

  const connect = useCallback(() => {
    if (!url || ws.current) return; // Don't connect if no URL or already connected/connecting

    console.log('[useWebSocket] Connecting...');
    ws.current = new WebSocket(url);
    setState(prev => ({ ...prev, isConnected: false, error: null })); // Indicate connecting attempt

    ws.current.onopen = (event) => {
      console.log('[useWebSocket] Connected');
      setState(prev => ({ ...prev, isConnected: true, error: null }));
      onOpen?.(event);
    };

    ws.current.onmessage = (event) => {
      // console.log('[useWebSocket] Message received:', event.data);
      setState(prev => ({ ...prev, lastMessage: event }));
      onMessage?.(event);
    };

    ws.current.onerror = (event) => {
      console.error('[useWebSocket] Error:', event);
      setState(prev => ({ ...prev, isConnected: false, error: event }));
      onError?.(event);
      // Consider closing here if not attempting reconnect
      ws.current = null;
    };

    ws.current.onclose = (event) => {
      console.log(`[useWebSocket] Disconnected. Code: ${event.code}, Reason: ${event.reason}`);
      // Only update state if it wasn't an error-triggered close handled above
      if (ws.current) { // Check ensures this wasn't called after manual close or error cleanup
         setState(prev => ({ ...prev, isConnected: false, error: null }));
         ws.current = null;
      }
      onClose?.(event);
      // Optional: Implement reconnect logic here
    };

  }, [url, onOpen, onMessage, onError, onClose]);

  const disconnect = useCallback(() => {
    if (ws.current) {
      console.log('[useWebSocket] Disconnecting...');
      ws.current.onclose = null; // Prevent onClose handler during manual disconnect
      ws.current.onerror = null;
      ws.current.onmessage = null;
      ws.current.onopen = null;
      ws.current.close();
      ws.current = null;
      setState(prev => ({ 
          ...prev, 
          isConnected: false, 
          error: null, 
          // lastMessage: null // debatable if we should clear last message on disconnect
      }));
    }
  }, []);

  useEffect(() => {
    if (url) {
      connect();
    } else {
      disconnect(); // Disconnect if URL becomes null
    }

    // Cleanup function on unmount or URL change
    return () => {
      disconnect();
    };
  }, [url, connect, disconnect]);

  const sendMessage = useCallback((data: string | ArrayBuffer | Blob | ArrayBufferView) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(data);
    } else {
      console.error('[useWebSocket] Cannot send message, WebSocket is not connected.');
      // Optionally throw an error or return a status
    }
  }, []);

  return {
    isConnected: state.isConnected,
    lastMessage: state.lastMessage,
    error: state.error,
    sendMessage,
    connect, // Expose connect/disconnect if manual control is needed
    disconnect,
  };
}; 