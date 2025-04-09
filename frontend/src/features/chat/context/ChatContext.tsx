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
import { saveAccessToken, saveRefreshToken } from '@/config/storage.config'

// Import context types from the correct file
import { ChatContextType, ChatState } from './ChatContext.types';
// Import API data/payload types from the correct file
import {
  Message,
  CreateChatPayload,
  CreateMessagePayload
} from '@/api/types/chat.types';
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

  // --- Direct API Call Functions ---

  const fetchChatList = useCallback(async () => {
    setState(prev => ({ ...prev, loadingChats: true, chatsError: null }));
    try {
      const response = await chatApi.getChats();
      setState(prev => ({
        ...prev,
        chatList: response.data,
        loadingChats: false,
      }));
    } catch (error) {
      console.error("Error fetching chats:", error);
      setState(prev => ({ 
        ...prev, 
        chatsError: error as ApiError, 
        loadingChats: false 
      }));
    }
  }, []);

  const fetchChatDetails = useCallback(async (chatId: string) => {
    setState(prev => ({ ...prev, loadingMessages: true, messagesError: null }));
    try {
      const response = await chatApi.getChatDetails(chatId);
      setState(prev => ({
        ...prev,
        messages: response.data.messages,
        loadingMessages: false,
      }));
    } catch (error) {
      console.error("Error fetching chat details:", error);
      setState(prev => ({ 
        ...prev, 
        messagesError: error as ApiError, 
        loadingMessages: false, 
        messages: null // Clear messages on error
      }));
    }
  }, []);

  const startNewChat = useCallback(async () => {
    if (state.creatingChat) return; // Prevent double clicks

    setState(prev => ({...prev, creatingChat: true, createChatError: null}));
    try {
      const payload: CreateChatPayload = { name: 'New Chat' };
      const response = await chatApi.createChat(payload);
      console.log("startNewChat: response:", response);
      // Check if response data and ID exist
      if (!response.data?._id) {
        console.error("startNewChat: Received invalid response from API.");
        throw new Error("Invalid response from server when creating chat."); 
      }
      
      const newChat = response.data;

      setState((prev: ChatState) => ({
        ...prev,
        chatList: [...(prev.chatList || []), newChat],
        creatingChat: false,
        createChatError: null,
        selectedChatId: newChat._id // Select the new chat
      }));
      
      // Navigate only on native platforms
      if (Platform.OS !== 'web') {
        router.push(`/chat/${newChat._id}` as any);
      }

    } catch (error) {
      console.error("Error creating chat:", error);
      setState(prev => ({ 
        ...prev, 
        createChatError: error as ApiError, 
        creatingChat: false 
      }));
    }
  }, [state.creatingChat, router]); // Add router dependency

  // --- WebSocket Effect (Remains the same) ---
  useEffect(() => {
    const closeExistingSocket = () => {
        if (ws.current) {
            console.log('Closing previous WebSocket connection...');
            ws.current.onclose = null; 
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
          const newMessage: Message = JSON.parse(event.data);
          setState(prev => ({
              ...prev,
              messages: prev.messages?.some(m => m._id === newMessage._id)
                  ? prev.messages
                  : [...(prev.messages || []), newMessage],
          }));
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      socket.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      socket.onclose = (event) => {
        console.log(`WebSocket disconnected from chat ${state.selectedChatId}. Code: ${event.code}, Reason: ${event.reason}`);
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

  // --- Actions (Simplified) ---

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
      // Set a generic error state matching ApiError structure
      setState(prev => ({ ...prev, sendMessageError: { message: 'Failed to send message', error_code: 'WS_SEND_ERROR', status_code: 0 } }));
    }
  }, [state.currentMessage, wsBaseUrl, setCurrentMessageText]); // Added setCurrentMessageText dependency

  // --- Fetching Effects (Using direct API calls now) ---

  // Fetch chat list on initial mount
  useEffect(() => {
    fetchChatList();
  }, [fetchChatList]); // fetchChatList is memoized

  // Fetch chat details when selectedChatId changes
  useEffect(() => {
    if (state.selectedChatId) {
      fetchChatDetails(state.selectedChatId);
    } else {
      // Clear messages if no chat is selected
      setState(prev => ({ ...prev, messages: null, loadingMessages: false, messagesError: null }));
    }
    // Ensure fetchChatDetails is included if it changes identity (it's memoized, so shouldn't)
  }, [state.selectedChatId, fetchChatDetails]); 

  // --- Context Value ---
  const value = useMemo(() => ({
    ...state,
    selectChat,
    sendMessage,
    setCurrentMessageText,
    startNewChat,
    fetchChatList, // Expose fetchChatList if manual refresh is needed
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
