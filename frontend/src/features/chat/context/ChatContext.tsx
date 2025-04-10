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
import { ChatContextType } from './ChatContext.types';
// Import API data/payload types from the correct file
import {
  Message,
  ChatListItem,
  CreateChatPayload,
  CreateMessagePayload
} from '@/api/types/chat.types';
import { ApiError } from '@/api/types/api.types';
import * as chatApi from '@/api/endpoints/chatApi';
import { config } from '@/config/environment.config'; // Import config for WS URL
import { getAccessToken } from '@/config/storage.config' // Import getAccessToken

// Remove single initialState object
// const initialState: ChatState = { ... };

const ChatContext = createContext<ChatContextType | null>(null);

interface ChatProviderProps {
  children: ReactNode;
}

export const ChatProvider: React.FC<ChatProviderProps> = ({ children }) => {
  // --- Individual State Hooks ---
  const [chatList, setChatList] = useState<ChatListItem[] | null>(null);
  const [messages, setMessages] = useState<Message[] | null>(null);
  const [selectedChatId, setSelectedChatId] = useState<string | null>(null);
  const [currentMessage, setCurrentMessage] = useState<string>('');
  const [loadingChats, setLoadingChats] = useState<boolean>(true); // Start loading initially
  const [loadingMessages, setLoadingMessages] = useState<boolean>(false);
  const [sendingMessage, setSendingMessage] = useState<boolean>(false);
  const [creatingChat, setCreatingChat] = useState<boolean>(false);
  const [chatsError, setChatsError] = useState<ApiError | null>(null);
  const [messagesError, setMessagesError] = useState<ApiError | null>(null);
  const [sendMessageError, setSendMessageError] = useState<ApiError | null>(null);
  const [createChatError, setCreateChatError] = useState<ApiError | null>(null);
  const [isWsConnected, setIsWsConnected] = useState<boolean>(false);
  // --- End Individual State Hooks ---

  const router = useRouter();
  const ws = useRef<WebSocket | null>(null); // Ref to hold WebSocket instance

  // Base WebSocket URL (replace http/https with ws/wss)
  const wsBaseUrl = config.API_URL.replace(/^http/, 'ws');

  // --- Direct API Call Functions (Update Setters) ---

  const fetchChatList = useCallback(async () => {
    setLoadingChats(true);
    setChatsError(null);
    try {
      const response = await chatApi.getChats();
      setChatList(response.data);
    } catch (error) {
      console.error("Error fetching chats:", error);
      setChatsError(error as ApiError);
    } finally {
      setLoadingChats(false);
    }
  }, []);

  const fetchChatDetails = useCallback(async (chatId: string) => {
    setLoadingMessages(true);
    setMessagesError(null);
    try {
      const response = await chatApi.getChatDetails(chatId);
      setMessages(response.data.messages);
    } catch (error) {
      console.error("Error fetching chat details:", error);
      setMessagesError(error as ApiError);
      setMessages(null); // Clear messages on error
    } finally {
      setLoadingMessages(false);
    }
  }, []);

  const startNewChat = useCallback(async () => {
    if (creatingChat) return;

    setCreatingChat(true);
    setCreateChatError(null);
    try {
      const payload: CreateChatPayload = { name: 'New Chat' };
      const response = await chatApi.createChat(payload);
      console.log("startNewChat: response:", response);

      if (!response.data?._id) {
        console.error("startNewChat: Received invalid response from API.");
        throw new Error("Invalid response from server when creating chat."); 
      }
      
      const newChat = response.data;
      
      // Update list and select
      setChatList(prevList => [...(prevList || []), newChat]);
      setSelectedChatId(newChat._id);
      
      // Navigate on native
      if (Platform.OS !== 'web') {
        router.push(`/chat/${newChat._id}` as any);
      }
    } catch (error) {
      console.error("Error creating chat:", error);
      setCreateChatError(error as ApiError);
    } finally {
      setCreatingChat(false);
    }
  }, [creatingChat, router]);

  // --- WebSocket Effect (Update Setters) ---
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
            setIsWsConnected(false); // Use individual setter
        }
    };

    const connectWebSocket = async () => {
      if (selectedChatId) { // Use state variable directly
        closeExistingSocket();
        const token = await getAccessToken();
        if (!token) {
          console.error("WebSocket: No auth token found, cannot connect.");
          return;
        }
        const wsUrl = `${wsBaseUrl}/chats/ws/${selectedChatId}?token=${encodeURIComponent(token)}`;
        try {
          const socket = new WebSocket(wsUrl);
          ws.current = socket;

          socket.onopen = () => {
            console.log(`WebSocket connected to chat ${selectedChatId}`);
            setIsWsConnected(true); // Use individual setter
          };

          socket.onmessage = (event) => {
            try {
              const newMessage: Message = JSON.parse(event.data);
              
              // Use functional update with individual setter
              setMessages(prevMessages => {
                  const alreadyExists = prevMessages?.some(m => m._id === newMessage._id);
                  if (alreadyExists) {
                      console.log('[WS] State unchanged (duplicate).');
                      return prevMessages; 
                  }
                  const newMessages = [...(prevMessages || []), newMessage];
                  return newMessages;
              });

            } catch (error) {
              console.error('[WS] Error parsing/processing message:', error);
            }
          };

          socket.onerror = (error) => {
            console.error('WebSocket error:', error);
            if (ws.current === socket) {
                setIsWsConnected(false); // Use individual setter
                ws.current = null; 
            }
          };

          socket.onclose = (event) => {
            console.log(`WebSocket disconnected from chat ${selectedChatId}. Code: ${event.code}, Reason: ${event.reason}`);
            if (ws.current === socket) {
                 setIsWsConnected(false); // Use individual setter
                 ws.current = null;
            }
          };
        } catch (error) {
           console.error("Error creating WebSocket:", error);
           setIsWsConnected(false); // Use individual setter
        }
      } else {
        closeExistingSocket();
      }
    }

    connectWebSocket();
    return () => closeExistingSocket();
  }, [selectedChatId, wsBaseUrl]); // Dependency: selectedChatId

  // --- Actions (Simplified, Use Setters) ---

  const setCurrentMessageText = useCallback((text: string) => {
    setCurrentMessage(text);
  }, []);

  const selectChat = useCallback((id: string) => {
    setSelectedChatId(id);
    if (Platform.OS !== 'web') {
      router.push(`/chat/${id}` as any);
    }
  }, [router]);

  const sendMessage = useCallback(async () => {
    if (currentMessage.trim() === '' || !ws.current || ws.current.readyState !== WebSocket.OPEN) {
        console.warn('WebSocket not connected or message empty. Cannot send.');
        setSendMessageError({ message: 'Not connected', error_code: 'WS_NOT_CONNECTED', status_code: 0 });
        return;
    }
    try {
      const payload: CreateMessagePayload = {
          content: currentMessage.trim(),
          sender_type: 'user'
      };
      console.log('Sending message via WebSocket:', JSON.stringify(payload));
      ws.current.send(JSON.stringify(payload));
      setCurrentMessage(''); // Use individual setter
      setSendMessageError(null); // Clear error on success
    } catch (error) {
      console.error("Error sending message via WebSocket:", error);
      setSendMessageError({ message: 'Failed to send message', error_code: 'WS_SEND_ERROR', status_code: 0 });
    }
  }, [currentMessage, wsBaseUrl]);

  // --- Fetching Effects (Update Setters) ---

  useEffect(() => {
    fetchChatList();
  }, [fetchChatList]);

  useEffect(() => {
    if (selectedChatId) { // Use state variable
      fetchChatDetails(selectedChatId);
    } else {
      setMessages(null);
      setLoadingMessages(false);
      setMessagesError(null);
    }
  }, [selectedChatId, fetchChatDetails]);

  return (
    <ChatContext.Provider value={
      {
        chatList,
        messages,
        selectedChatId,
        currentMessage,
        loadingChats,
        loadingMessages,
        sendingMessage,
        creatingChat,
        chatsError,
        messagesError,
        sendMessageError,
        createChatError,
        isWsConnected,
        selectChat,
        sendMessage,
        setCurrentMessageText,
        startNewChat,
        fetchChatList,
        setSelectedChatId
      }
    }>
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
