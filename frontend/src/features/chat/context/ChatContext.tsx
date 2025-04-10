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

import { ChatContextType } from './ChatContext.types';
import {
  Message,
  Chat,
  PaginatedResponseData,
} from '@/api/types/chat.types';

// Import custom hooks
import { useChatApi } from '../hooks/useChatApi';
import { useChatWebSocket } from '../hooks/useChatWebSocket';

const ChatContext = createContext<ChatContextType | null>(null);

interface ChatProviderProps {
  children: ReactNode;
}

export const ChatProvider: React.FC<ChatProviderProps> = ({ children }) => {
  const router = useRouter();

  // --- Core State managed directly by Context ---
  const [chatListData, setChatListData] = useState<PaginatedResponseData<Chat> | null>(null);
  const [messageData, setMessageData] = useState<PaginatedResponseData<Message> | null>(null);
  const [selectedChatId, setSelectedChatId] = useState<string | null>(null);
  const [currentMessage, setCurrentMessage] = useState<string>('');

  // --- API Hook ---
  const {
      // API Loading States
      loadingChats,
      loadingMessages,
      creatingChat,
      updatingChat,
      loadingMoreChats,
      loadingMoreMessages,
      // API Error States
      chatsError,
      messagesError,
      createChatError,
      updateChatError,
      // API Actions
      fetchChatList,
      fetchMoreChats,
      fetchMessages,
      fetchMoreMessages,
      startNewChat,
      updateChat,
  } = useChatApi({
      setChatListData,
      setMessageData,
      setSelectedChatId
  });

  // --- Use the enhanced useChatWebSocket hook ---
  const {
      isConnected,
      connectionError,
      parseError,
      sendingMessage,
      sendMessageError,
      sendChatMessage: sendWsMessage,
  } = useChatWebSocket({
      selectedChatId,
      setChatListData,
      setMessageData,
  });

  // --- Actions managed by Context ---
  const setCurrentMessageText = useCallback((text: string) => {
    setCurrentMessage(text);
  }, []);

  const selectChat = useCallback((id: string) => {
    if (id !== selectedChatId) {
        setSelectedChatId(id);
        setMessageData(null);
    }
    if (Platform.OS !== 'web') {
      router.push(`/chat/${id}` as any);
    }
  }, [router, selectedChatId, setSelectedChatId]);

  const sendMessage = useCallback(async () => {
     const result = await sendWsMessage({ 
         content: currentMessage.trim(), 
         sender_type: 'user' 
     });
     if (result.success) {
        setCurrentMessage(''); 
     }
  }, [sendWsMessage, currentMessage, setCurrentMessage]);

  const fetchMoreChatsContext = useCallback(() => {
      fetchMoreChats(chatListData);
  }, [fetchMoreChats, chatListData]);

  const fetchMessagesContext = useCallback((chatId: string) => {
      fetchMessages(chatId);
  }, [fetchMessages]);

  const fetchMoreMessagesContext = useCallback(() => {
      if (!selectedChatId) return;
      fetchMoreMessages(selectedChatId, messageData);
  }, [fetchMoreMessages, selectedChatId, messageData]);

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

  // --- Context Value (adjust based on returned values from useChatWebSocket) ---
  const value: ChatContextType = useMemo(() => ({
    // Context State
    chatListData,
    messageData,
    selectedChatId,
    currentMessage,
    // API Hook State
    loadingChats,
    chatsError,
    loadingMessages,
    messagesError,
    creatingChat,
    createChatError,
    loadingMoreChats,
    loadingMoreMessages,
    updatingChat,
    updateChatError,
    // WebSocket Hook State
    isWsConnected: isConnected,
    wsConnectionError: connectionError,
    wsParseError: parseError,
    sendingMessage,
    sendMessageError,
    // Context Actions
    selectChat,
    sendMessage,
    setCurrentMessageText,
    setSelectedChatId,
    // API Hook Actions
    startNewChat,
    updateChat,
    fetchChatList,
    // Context Action Wrappers for API
    fetchMoreChats: fetchMoreChatsContext,
    fetchMessages: fetchMessagesContext,
    fetchMoreMessages: fetchMoreMessagesContext,
  }), [
      // Context State
      chatListData, messageData, selectedChatId, currentMessage,
      // API Hook State/Actions
      loadingChats, chatsError, loadingMessages, messagesError, creatingChat,
      createChatError, loadingMoreChats, loadingMoreMessages, updatingChat, updateChatError,
      fetchChatList, startNewChat, updateChat, fetchMoreChats, fetchMessages, fetchMoreMessages,
      // WebSocket Hook State (use correct destructured names)
      isConnected, connectionError, parseError, sendingMessage, sendMessageError, 
      // Context Actions / Hook Wrappers
      selectChat, sendMessage, setCurrentMessageText, setSelectedChatId,
      fetchMoreChatsContext, fetchMessagesContext, fetchMoreMessagesContext
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
