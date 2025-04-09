import React, {
  createContext,
  useState,
  useContext,
  ReactNode,
  useMemo,
  useEffect,
  useCallback,
  useRef,
} from 'react';
import { Platform } from 'react-native';
import { useRouter } from 'expo-router';

// Import context types from the correct file
import { ChatContextType, ChatState } from './ChatContext.types';
// Import API data/payload types from the correct file
import {
  MessageData,
  ChatListItemData,
  ChatDetailData,
  CreateChatPayload,
  CreateMessagePayload
} from '@/api/types/chat.types';
import { useApi } from '@/api/useApi';
import { ApiError } from '@/api/types/api.types';
import * as chatApi from '@/api/endpoints/chatApi';
import { config } from '@/config/environment.config'; // Import config for WS URL

// Initial state including WebSocket status
const initialState: ChatState = {
  chatList: null,
  messages: null,
  selectedChatId: null,
  currentMessage: '',
  loadingChats: true,
  loadingMessages: false,
  sendingMessage: false,
  creatingChat: false,
  chatsError: null,
  messagesError: null,
  sendMessageError: null,
  createChatError: null,
  isWsConnected: false, // Initial WS state
};

const ChatContext = createContext<ChatContextType | null>(null);

interface ChatProviderProps {
  children: ReactNode;
}

export const ChatProvider: React.FC<ChatProviderProps> = ({ children }) => {
  const [state, setState] = useState<ChatState>(initialState);
  const router = useRouter();
  const ws = useRef<WebSocket | null>(null); // Ref to hold WebSocket instance

  // Base WebSocket URL (replace http/https with ws/wss)
  const wsBaseUrl = config.API_URL.replace(/^http/, 'ws');

  // --- Memoized Callbacks for useApi --- 
  const handleFetchChatsSuccess = useCallback((data: ChatListItemData[]) => {
    setState((prev: ChatState) => ({
      ...prev,
      chatList: data,
      loadingChats: false,
      chatsError: null,
    }));
  }, []);

  const handleFetchChatsError = useCallback((error: ApiError) => {
    console.error("Error fetching chats:", error);
    setState((prev: ChatState) => ({ ...prev, chatsError: error, loadingChats: false }));
  }, []);

  const handleFetchDetailsSuccess = useCallback((data: ChatDetailData) => {
    setState((prev: ChatState) => ({
      ...prev,
      messages: data.messages,
      loadingMessages: false,
      messagesError: null,
    }));
  }, []);

  const handleFetchDetailsError = useCallback((error: ApiError) => {
    console.error("Error fetching chat details:", error);
    setState((prev: ChatState) => ({ ...prev, messagesError: error, loadingMessages: false, messages: null }));
  }, []);

  const handleAddMessageSuccess = useCallback((newMessage: MessageData) => {
    console.log("REST addMessage succeeded (fallback?):", newMessage);
    setState((prev: ChatState) => ({
      ...prev,
      sendingMessage: false,
      sendMessageError: null,
    }));
    setCurrentMessageText('');
  }, []); // Note: setCurrentMessageText is already memoized

  const handleAddMessageError = useCallback((error: ApiError) => {
    console.error("Error sending message via REST (fallback?):", error);
    setState((prev: ChatState) => ({ ...prev, sendMessageError: error, sendingMessage: false }));
  }, []);

  const handleCreateChatSuccess = useCallback((newChat: ChatListItemData) => {
    setState((prev: ChatState) => ({
      ...prev,
      chatList: prev.chatList ? [...prev.chatList, newChat] : [newChat],
      creatingChat: false,
      createChatError: null,
      selectedChatId: newChat.id
    }));
    router.push(`/chat/${newChat.id}` as any);
  }, [router]); // Include router as dependency

  const handleCreateChatError = useCallback((error: ApiError) => {
    console.error("Error creating chat:", error);
    setState((prev: ChatState) => ({ ...prev, createChatError: error, creatingChat: false }));
  }, []);

  // --- REST API Hooks (use memoized callbacks) ---
  const {
    execute: fetchChatsApi,
  } = useApi<ChatListItemData[], []>(chatApi.getChats, {
    onSuccess: handleFetchChatsSuccess,
    onError: handleFetchChatsError,
  });

  const {
    execute: fetchChatDetailsApi,
  } = useApi<ChatDetailData, [string]>(chatApi.getChatDetails, {
    onSuccess: handleFetchDetailsSuccess,
    onError: handleFetchDetailsError,
  });

  const {
    execute: addMessageApi,
  } = useApi<MessageData, [string, CreateMessagePayload]>(chatApi.addMessage, {
    onSuccess: handleAddMessageSuccess,
    onError: handleAddMessageError,
  });

  const {
      execute: createChatApi,
  } = useApi<ChatListItemData, [CreateChatPayload]>(chatApi.createChat, {
      onSuccess: handleCreateChatSuccess,
      onError: handleCreateChatError,
  });

  // --- WebSocket Effect ---
  useEffect(() => {
    const closeExistingSocket = () => {
        if (ws.current) {
            console.log('Closing previous WebSocket connection...');
            ws.current.onclose = null; // Prevent onclose handler from firing on manual close
            ws.current.onerror = null;
            ws.current.onmessage = null;
            ws.current.onopen = null;
            ws.current.close();
            ws.current = null;
            setState(prev => ({ ...prev, isWsConnected: false }));
        }
    };

    if (state.selectedChatId) {
      closeExistingSocket();
      const wsUrl = `${wsBaseUrl}/chats/ws/${state.selectedChatId}`;
      console.log(`Connecting WebSocket to: ${wsUrl}`);
      const socket = new WebSocket(wsUrl);
      ws.current = socket;

      socket.onopen = () => {
        console.log(`WebSocket connected to chat ${state.selectedChatId}`);
        setState(prev => ({ ...prev, isWsConnected: true }));
      };

      socket.onmessage = (event) => {
        try {
          console.log('WebSocket message received:', event.data);
          const newMessage: MessageData = JSON.parse(event.data);
          setState(prev => ({
              ...prev,
              messages: prev.messages?.some(m => m.id === newMessage.id)
                  ? prev.messages
                  : [...(prev.messages || []), newMessage],
          }));
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      socket.onerror = (error) => {
        console.error('WebSocket error:', error);
        // Maybe set a specific WS error state?
      };

      socket.onclose = (event) => {
        console.log(`WebSocket disconnected from chat ${state.selectedChatId}. Code: ${event.code}, Reason: ${event.reason}`);
        // Only update state if the closure wasn't initiated by us
        if (ws.current === socket) {
             setState(prev => ({ ...prev, isWsConnected: false }));
             ws.current = null;
        }
      };

    } else {
      closeExistingSocket();
    }

    return () => {
      closeExistingSocket();
    };
  }, [state.selectedChatId, wsBaseUrl]);

  // --- Actions (Modified sendMessage) ---

  // Define setCurrentMessageText first
  const setCurrentMessageText = useCallback((text: string) => {
    setState(prev => ({ ...prev, currentMessage: text }));
  }, []);

  const selectChat = useCallback((id: string) => {
    if (Platform.OS === 'web') {
      setState(prev => ({ ...prev, selectedChatId: id }));
    } else {
      router.push(`/chat/${id}` as any);
    }
  }, [router]);

  // Now define sendMessage, which uses setCurrentMessageText
  const sendMessage = useCallback(async () => {
    if (state.currentMessage.trim() === '' || !ws.current || ws.current.readyState !== WebSocket.OPEN) {
        console.warn('WebSocket not connected or message empty. Cannot send.');
        setState(prev => ({ ...prev, sendMessageError: { message: 'Not connected', error_code: 'WS_NOT_CONNECTED', status_code: 0 }}));
        return;
    }

    try {
      const payload: CreateMessagePayload = {
          content: state.currentMessage.trim(),
          sender_type: 'user'
      };
      console.log('Sending message via WebSocket:', JSON.stringify(payload));
      ws.current.send(JSON.stringify(payload));
      setCurrentMessageText(''); // Clear input after sending
    } catch (error) {
      console.error("Error sending message via WebSocket:", error);
      setState(prev => ({ ...prev, sendMessageError: { message: 'Failed to send', error_code: 'WS_SEND_ERROR', status_code: 0 } }));
    }
  }, [state.currentMessage, wsBaseUrl, setCurrentMessageText]); // Dependency correct

  const startNewChat = useCallback(async (name?: string | null) => {
      if (state.creatingChat) return;
      setState(prev => ({...prev, creatingChat: true, createChatError: null}));
      try {
          await createChatApi({ name });
      } catch (error) {
           console.log("Create chat caught error (likely handled by useApi):", error);
      }
  }, [state.creatingChat, createChatApi]);

  const fetchChatList = useCallback(() => {
      setState(prev => ({ ...prev, loadingChats: true, chatsError: null }));
      fetchChatsApi();
  }, [fetchChatsApi]);

  // --- Fetching Effects ---

  // Fetch chat list on initial mount
  useEffect(() => {
    fetchChatList();
  }, [fetchChatList]);

  // Fetch chat details when selectedChatId changes
  useEffect(() => {
    if (state.selectedChatId) {
      setState(prev => ({ ...prev, loadingMessages: true, messagesError: null }));
      fetchChatDetailsApi(state.selectedChatId);
    } else {
      // Clear messages if no chat is selected
      setState(prev => ({ ...prev, messages: null, loadingMessages: false, messagesError: null }));
    }
  }, [state.selectedChatId, fetchChatDetailsApi]);

  // --- Context Value ---
  const value = useMemo(() => ({
    ...state,
    // Use state values directly now, managed internally
    selectChat,
    sendMessage,
    setCurrentMessageText,
    startNewChat,
    fetchChatList,
  }), [
      state,
      selectChat, sendMessage, setCurrentMessageText, startNewChat, fetchChatList
  ]);

  return (
    <ChatContext.Provider value={value}>
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = (): ChatContextType => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};
