import React, {
  createContext,
  useState,
  useContext,
  ReactNode,
  useMemo,
  useEffect,
  useCallback,
} from 'react';
import { Platform } from 'react-native';
import { useRouter } from 'expo-router';

import { useApi } from '@/api/useApi';
import { ChatContextType } from './ChatContext.types';
import {
  Message,
  ChatListItem,
  Chat,
  CreateChatPayload,
  CreateMessagePayload
} from '@/api/types/chat.types';
import { ApiError } from '@/api/types/api.types';
import * as chatApi from '@/api/endpoints/chatApi';

// Import the new hook
import { useChatWebSocket } from '../hooks/useChatWebSocket';

const ChatContext = createContext<ChatContextType | null>(null);

interface ChatProviderProps {
  children: ReactNode;
}

export const ChatProvider: React.FC<ChatProviderProps> = ({ children }) => {
  // --- State Hooks (Keep data, remove loading/error) ---
  const [chatList, setChatList] = useState<ChatListItem[] | null>(null);
  const [messages, setMessages] = useState<Message[] | null>(null);
  const [selectedChatId, setSelectedChatId] = useState<string | null>(null);
  const [currentMessage, setCurrentMessage] = useState<string>('');
  
  // State for the send action itself (pending/error)
  const [sendingMessage, setSendingMessage] = useState<boolean>(false);
  const [sendMessageError, setSendMessageError] = useState<ApiError | null>(null);
  // --- End State Hooks ---

  const router = useRouter();

  // --- Memoized Callbacks for useApi Hooks ---
  const handleGetChatsSuccess = useCallback((data: ChatListItem[]) => { 
    setChatList(data); 
  }, []);

  const handleGetChatsError = useCallback((error: ApiError) => {
    console.error("Error fetching chats:", error);
  }, []);

  const handleGetDetailsSuccess = useCallback((data: Chat) => { 
    setMessages(data.messages); 
  }, []);

  const handleGetDetailsError = useCallback((error: ApiError) => {
    console.error("Error fetching chat details:", error);
    setMessages(null);
  }, []);

  const handleCreateChatSuccess = useCallback((newChat: Chat) => { 
      if (!newChat?._id) {
        console.error("startNewChat: Received invalid chat data from API hook.");
        return; 
      }
      setChatList(prevList => [...(prevList || []), newChat]);
      setSelectedChatId(newChat._id);
      if (Platform.OS !== 'web') {
        router.push(`/chat/${newChat._id}` as any);
      }
  }, [router]);

  const handleCreateChatError = useCallback((error: ApiError) => {
    console.error("Error creating chat:", error);
  }, []);

  // --- useApi Hooks --- 
  const { 
    execute: fetchChatsApi, 
    loading: loadingChats, 
    error: chatsError, 
    reset: resetChatsError 
  } = useApi<ChatListItem[], []>(chatApi.getChats, {
    onSuccess: handleGetChatsSuccess,
    onError: handleGetChatsError,
  });

  const { 
    execute: fetchDetailsApi, 
    loading: loadingMessages, 
    error: messagesError, 
    reset: resetMessagesError 
  } = useApi<Chat, [string]>(chatApi.getChatDetails, {
    onSuccess: handleGetDetailsSuccess,
    onError: handleGetDetailsError,
  });

  const { 
    execute: createChatApi, 
    loading: creatingChat, 
    error: createChatError, 
    reset: resetCreateChatError 
  } = useApi<Chat, [CreateChatPayload]>(chatApi.createChat, {
      onSuccess: handleCreateChatSuccess,
      onError: handleCreateChatError,
  });

  // --- WebSocket Hook --- 
  const handleWebSocketMessage = useCallback((newMessage: Message) => {
     setMessages(prevMessages => {
        const alreadyExists = prevMessages?.some(m => m._id === newMessage._id);
        if (alreadyExists) {
            console.log('[WS Context Handler] State unchanged (duplicate).');
            return prevMessages; 
        }
        console.log('[WS Context Handler] Adding new message:', newMessage._id);
        return [...(prevMessages || []), newMessage];
     });
  }, []);

  const {
      isConnected: isWsConnected,
      connectionError: wsConnectionError,
      parseError: wsParseError,
      sendChatMessage,
  } = useChatWebSocket(selectedChatId, {
      onMessageReceived: handleWebSocketMessage,
  });

  // --- Actions --- 

  const setCurrentMessageText = useCallback((text: string) => {
    setCurrentMessage(text);
  }, []);

  const selectChat = useCallback((id: string) => {
    setSelectedChatId(id);
    resetMessagesError(); 
    if (Platform.OS !== 'web') {
      router.push(`/chat/${id}` as any);
    }
  }, [router, resetMessagesError]);

  // Updated sendMessage action
  const sendMessage = useCallback(async () => {
     if (currentMessage.trim() === '') {
        console.warn('Message empty. Cannot send.');
        return;
    }
     if (!isWsConnected) {
        console.warn('WebSocket not connected. Cannot send.');
        setSendMessageError({ message: 'Not connected', error_code: 'WS_NOT_CONNECTED', status_code: 0 });
        return;
    }
    
    setSendingMessage(true);
    setSendMessageError(null);
    
    try {
      const payload: CreateMessagePayload = {
          content: currentMessage.trim(),
          sender_type: 'user'
      };
      console.log('Sending message via useChatWebSocket:', JSON.stringify(payload));
      sendChatMessage(payload); // Use the hook's send function
      setCurrentMessage(''); 
      setSendingMessage(false); 
    } catch (error) {
      console.error("Error preparing/sending message:", error);
      setSendMessageError({
         message: error instanceof Error ? error.message : 'Failed to send message',
         error_code: 'WS_SEND_ACTION_ERROR',
         status_code: 0 
      });
      setSendingMessage(false);
    }
  }, [currentMessage, isWsConnected, sendChatMessage]);

  const fetchChatList = useCallback(() => {
      resetChatsError();
      fetchChatsApi();
  }, [fetchChatsApi, resetChatsError]);

  const startNewChat = useCallback(async () => {
      resetCreateChatError();
      try {
        await createChatApi({ name: 'New Chat' }); 
      } catch (error) {
        console.log("startNewChat caught error (should be handled by useApi onError)", error);
      }
  }, [createChatApi, resetCreateChatError]);

  // --- Fetching Effects ---

  // Fetch chat list on initial mount
  useEffect(() => {
    fetchChatList();
  }, [fetchChatList]);

  // Fetch chat details when selectedChatId changes
  useEffect(() => {
    if (selectedChatId) {
      fetchDetailsApi(selectedChatId);
    } else {
      setMessages(null);
    }
  }, [selectedChatId, fetchDetailsApi]);

  // --- Context Value ---
  const value: ChatContextType = useMemo(() => ({
    // State
    chatList,
    messages,
    selectedChatId,
    currentMessage,
    // State from useApi hooks
    loadingChats,
    chatsError,
    loadingMessages,
    messagesError,
    creatingChat,
    createChatError,
    // State from useChatWebSocket hook
    isWsConnected,
    wsConnectionError,
    wsParseError,
    // State for send action
    sendingMessage,
    sendMessageError,
    // Actions
    selectChat,
    sendMessage,
    setCurrentMessageText,
    startNewChat,
    fetchChatList,
    setSelectedChatId,
  }), [
      // Dependencies: all state vars & actions
      chatList, messages, selectedChatId, currentMessage, isWsConnected,
      loadingChats, chatsError, loadingMessages, messagesError, creatingChat,
      createChatError, wsConnectionError, wsParseError, sendingMessage, sendMessageError,
      selectChat, sendMessage, setCurrentMessageText, startNewChat, fetchChatList,
      setSelectedChatId
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
