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
  Chat,
  CreateChatPayload,
  CreateMessagePayload,
  PaginatedResponseData,
  PaginationParams,
} from '@/api/types/chat.types';
import { ApiError } from '@/api/types/api.types';
import * as chatApi from '@/api/endpoints/chatApi';
import { useChatWebSocket } from '../hooks/useChatWebSocket';

import { 
    GetChatsData, 
    GetChatMessagesData, 
    CreateChatData
} from '@/api/endpoints/chatApi';

const ChatContext = createContext<ChatContextType | null>(null);

interface ChatProviderProps {
  children: ReactNode;
}

export const ChatProvider: React.FC<ChatProviderProps> = ({ children }) => {
  // --- State Hooks ---
  const [chatListData, setChatListData] = useState<PaginatedResponseData<Chat> | null>(null);
  const [messageData, setMessageData] = useState<PaginatedResponseData<Message> | null>(null);
  const [selectedChatId, setSelectedChatId] = useState<string | null>(null);
  const [currentMessage, setCurrentMessage] = useState<string>('');
  const [sendingMessage, setSendingMessage] = useState<boolean>(false);
  const [sendMessageError, setSendMessageError] = useState<ApiError | null>(null);
  const [loadingMoreChats, setLoadingMoreChats] = useState<boolean>(false);
  const [loadingMoreMessages, setLoadingMoreMessages] = useState<boolean>(false);
  // --- End State Hooks ---

  const router = useRouter();

  // --- Memoized Callbacks for useApi Hooks ---
  const handleGetChatsSuccess = useCallback((data: GetChatsData, args?: PaginationParams[]) => {
    const isFetchingMore = !!args?.[0]?.before_timestamp;
    setChatListData(prevData => {
        if (isFetchingMore && prevData) {
            return {
                items: [...prevData.items, ...data.items],
                next_cursor_timestamp: data.next_cursor_timestamp,
                has_more: data.has_more,
            };
        } else {
            return data;
        }
    });
    if (isFetchingMore) {
      setLoadingMoreChats(false);
    }
  }, []);

  const handleGetChatsError = useCallback((error: ApiError, args?: PaginationParams[]) => {
    const isFetchingMore = !!args?.[0]?.before_timestamp;
    console.error(`Error fetching chats${isFetchingMore ? ' (more)' : ''}:`, error);
    if (isFetchingMore) {
      setLoadingMoreChats(false);
    }
  }, []);

  const handleGetMessagesSuccess = useCallback((data: GetChatMessagesData, args?: [string, PaginationParams]) => {
    const isFetchingMore = !!args?.[1]?.before_timestamp;
    setMessageData(prevData => {
        if (isFetchingMore && prevData) {
            return {
                items: [...data.items, ...prevData.items],
                next_cursor_timestamp: data.next_cursor_timestamp,
                has_more: data.has_more,
            };
        } else {
            return data;
        }
    });
     if (isFetchingMore) {
      setLoadingMoreMessages(false);
    }
  }, []);

  const handleGetMessagesError = useCallback((error: ApiError, args?: [string, PaginationParams]) => {
     const isFetchingMore = !!args?.[1]?.before_timestamp;
     console.error(`Error fetching messages${isFetchingMore ? ' (more)' : ''} for chat ${args?.[0]}:`, error);
     if (isFetchingMore) {
       setLoadingMoreMessages(false);
     }
  }, []);

  const handleCreateChatSuccess = useCallback((newChatData: CreateChatData) => { 
      setChatListData(prevData => {
          const newItem: Chat = newChatData;
          return {
              items: [newItem, ...(prevData?.items || [])],
              next_cursor_timestamp: prevData?.next_cursor_timestamp ?? null, 
              has_more: prevData?.has_more ?? false 
          };
      });
      setSelectedChatId(newChatData._id);
      if (Platform.OS !== 'web') {
        router.push(`/chat/${newChatData._id}` as any);
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
  } = useApi<GetChatsData, [PaginationParams?]>(chatApi.getChats, {
    onSuccess: handleGetChatsSuccess,
    onError: handleGetChatsError,
  });

  const { 
    execute: fetchMessagesApi, 
    loading: loadingMessages,
    error: messagesError, 
    reset: resetMessagesError 
  } = useApi<GetChatMessagesData, [string, PaginationParams?]>(chatApi.getChatMessages, {
    onSuccess: handleGetMessagesSuccess,
    onError: handleGetMessagesError,
  });

  const { 
    execute: createChatApi, 
    loading: creatingChat, 
    error: createChatError, 
    reset: resetCreateChatError 
  } = useApi<CreateChatData, [CreateChatPayload]>(chatApi.createChat, {
      onSuccess: handleCreateChatSuccess,
      onError: handleCreateChatError,
  });

  // --- WebSocket Hook --- 
  const handleWebSocketMessage = useCallback((newMessage: Message) => {
     setMessageData(prevData => {
        if (!prevData || !selectedChatId) return prevData;
        
        const alreadyExists = prevData.items.some(m => m._id === newMessage._id);
        if (alreadyExists) {
            console.log('[WS Context Handler] State unchanged (duplicate).');
            return prevData; 
        }
        console.log('[WS Context Handler] Adding new message via WS:', newMessage._id);
        return {
            ...prevData,
            items: [newMessage, ...prevData.items],
        };
     });
  }, [selectedChatId]);

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
    // Only clear messages if the chat ID is actually changing
    if (id !== selectedChatId) {
        setSelectedChatId(id);
        setMessageData(null);
        resetMessagesError();
    } else {
        setSelectedChatId(id);
    }
    
    if (Platform.OS !== 'web') {
      router.push(`/chat/${id}` as any);
    }
  }, [router, resetMessagesError, selectedChatId]);

  const sendMessage = useCallback(async () => {
     if (currentMessage.trim() === '') return;
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
      sendChatMessage(payload);
      setCurrentMessage(''); 
      setSendingMessage(false);
    } catch (error) {
      console.error("Error preparing/sending message:", error);
      setSendMessageError({ message: 'Failed to send message', error_code: 'WS_SEND_ACTION_ERROR', status_code: 0 });
      setSendingMessage(false);
    }
  }, [currentMessage, isWsConnected, sendChatMessage]);

  const fetchChatList = useCallback(() => {
      resetChatsError();
      fetchChatsApi({});
  }, [fetchChatsApi, resetChatsError]);

  const fetchMoreChats = useCallback(() => {
    if (loadingChats || loadingMoreChats || !chatListData?.has_more || !chatListData.next_cursor_timestamp) {
      return;
    }
    setLoadingMoreChats(true);
    fetchChatsApi({ before_timestamp: chatListData.next_cursor_timestamp });
  }, [loadingChats, loadingMoreChats, chatListData, fetchChatsApi]);

  const fetchMessages = useCallback((chatId: string) => {
      resetMessagesError();
      setMessageData(null);
      fetchMessagesApi(chatId, {});
  }, [fetchMessagesApi, resetMessagesError]);

  const fetchMoreMessages = useCallback(() => {
      if (!selectedChatId || loadingMessages || loadingMoreMessages || !messageData?.has_more || !messageData.next_cursor_timestamp) {
          return;
      }
      setLoadingMoreMessages(true);
      fetchMessagesApi(selectedChatId, { before_timestamp: messageData.next_cursor_timestamp });
  }, [selectedChatId, loadingMessages, loadingMoreMessages, messageData, fetchMessagesApi]);

  const startNewChat = useCallback(async () => {
      resetCreateChatError();
      try {
        await createChatApi({ name: 'New Chat' }); 
      } catch (error) {
        // Error handled by useApi hook
      }
  }, [createChatApi, resetCreateChatError]);

  // --- Fetching Effects ---

  useEffect(() => {
    fetchChatList();
  }, [fetchChatList]);

  useEffect(() => {
    if (selectedChatId) {
      fetchMessages(selectedChatId);
    } else {
      setMessageData(null);
    }
  }, [selectedChatId, fetchMessages]);

  // --- Context Value ---
  const value: ChatContextType = useMemo(() => ({
    // State
    chatListData,
    messageData,
    selectedChatId,
    currentMessage,
    // Loading/Error States
    loadingChats,
    chatsError,
    loadingMessages,
    messagesError,
    creatingChat,
    createChatError,
    loadingMoreChats,
    loadingMoreMessages,
    // WS State
    isWsConnected,
    wsConnectionError,
    wsParseError,
    // Send Action State
    sendingMessage,
    sendMessageError,
    // Actions
    selectChat,
    sendMessage,
    setCurrentMessageText,
    startNewChat,
    fetchChatList,
    fetchMoreChats,
    fetchMessages,
    fetchMoreMessages,
    setSelectedChatId,
  }), [
      chatListData, messageData, selectedChatId, currentMessage, isWsConnected,
      loadingChats, chatsError, loadingMessages, messagesError, creatingChat,
      createChatError, wsConnectionError, wsParseError, sendingMessage, sendMessageError,
      loadingMoreChats, loadingMoreMessages,
      selectChat, sendMessage, setCurrentMessageText, startNewChat, 
      fetchChatList, fetchMoreChats, fetchMessages, fetchMoreMessages, 
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
