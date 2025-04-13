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

const generateTemporaryId = () => `temp-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;

export const ChatProvider: React.FC<ChatProviderProps> = ({ children }) => {
  const router = useRouter();

  // --- Core State managed directly by Context ---
  const [messageData, setMessageData] = useState<PaginatedResponseData<Message> | null>(null);
  const [selectedChatId, setSelectedChatId] = useState<string | null>(null);
  const [currentMessage, setCurrentMessage] = useState<string>('');

  // --- API Hook ---
  const {
      chatListData,
      loadingChats,
      loadingMessages,
      loadingMoreMessages,
      creatingChat,
      updatingChat,
      loadingMoreChats,
      chatsError,
      messagesError,
      createChatError,
      updateChatError,
      screenshots,
      loadingScreenshots,
      screenshotsError,
      fetchChatList,
      fetchMoreChats,
      fetchMessages,
      fetchMoreMessages,
      startNewChat,
      updateChat,
      refreshMessages,
      fetchScreenshots,
  } = useChatApi({
      messageData,
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
    const trimmedMessage = currentMessage.trim();
    if (!trimmedMessage) return;

    // 1. Create temporary message
    const tempId = generateTemporaryId();
    const temporaryUserMessage: Message = {
      _id: tempId,
      sender_type: 'user',
      content: trimmedMessage,
      author_id: undefined,
      created_at: new Date().toISOString(),
      type: 'text',
      tool_name: undefined,
      isTemporary: true,
    };
    // Also create a temporary thinking message
    const temporaryThinkingMessage: Message = {
      _id: `thinking-${tempId}`, // Unique ID for thinking message
      sender_type: 'agent',
      content: "",
      created_at: new Date().toISOString(),
      type: 'thinking',
      isTemporary: true, // Mark as temporary
    };

    // 2. Optimistically update the UI with both user and thinking messages
    setMessageData(prevData => {
      const newItems = [temporaryThinkingMessage, temporaryUserMessage];
      if (!prevData) return { items: newItems, has_more: false, next_cursor_timestamp: null };
      return {
        ...prevData,
        // Prepend both new messages
        items: [...newItems, ...prevData.items],
      };
    });

    // 3. Clear the input field
    setCurrentMessage('');

    // 4. Send message to backend
    const result = await sendWsMessage({
      content: trimmedMessage,
      sender_type: 'user',
    });

    // 5. Handle send errors
    if (!result.success) {
      console.error("Failed to send message via WS:", result.error);
      // Update the temporary message state to show an error
      setMessageData(prevData => {
          if (!prevData) return prevData; // Should not happen
          return {
              ...prevData,
              items: prevData.items.map(msg => 
                  msg._id === tempId ? { ...msg, sendError: true, isTemporary: false } : msg
              ),
          };
      });
    }

  }, [sendWsMessage, currentMessage, setCurrentMessage, setMessageData]);

  const fetchMoreChatsContext = useCallback(() => {
      fetchMoreChats();
  }, [fetchMoreChats]);

  const fetchMessagesContext = useCallback((chatId: string) => {
      fetchMessages(chatId);
  }, [fetchMessages]);

  const fetchMoreMessagesContext = useCallback(() => {
      if (!selectedChatId) return;
      fetchMoreMessages(selectedChatId);
  }, [fetchMoreMessages, selectedChatId]);

  // Wrapper for refreshing the chat list
  const refreshChatListContext = useCallback(() => {
      fetchChatList({}, true); // Call fetch from useApiPaginated with isRefresh=true
  }, [fetchChatList]);

  // Wrapper for refreshing messages
  const refreshMessagesContext = useCallback(() => {
      if (!selectedChatId) return;
      refreshMessages(selectedChatId);
  }, [refreshMessages, selectedChatId]);

  useEffect(() => {
    fetchChatList();
  }, [fetchChatList]);

  useEffect(() => {
    if (selectedChatId) {
      fetchMessagesContext(selectedChatId);
    } else {
      setMessageData(null);
    }
  }, [selectedChatId, fetchMessagesContext]);

  // --- Context Value (adjust based on returned values from useChatWebSocket) ---
  const value: ChatContextType = useMemo(() => {
    return {
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
    screenshots,
    loadingScreenshots,
    screenshotsError,
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
    fetchScreenshots,
    fetchChatList,
    // Context Action Wrappers for API
    fetchMoreChats: fetchMoreChatsContext,
    refreshChatList: refreshChatListContext,
    fetchMessages: fetchMessagesContext,
    fetchMoreMessages: fetchMoreMessagesContext,
    refreshMessages: refreshMessagesContext,
  };
  }, [
      // Context State
      chatListData, messageData, selectedChatId, currentMessage,
      // API Hook State/Actions
      loadingChats, chatsError, loadingMessages, messagesError, creatingChat,
      createChatError, loadingMoreChats, loadingMoreMessages, updatingChat, updateChatError,
      screenshots, loadingScreenshots, screenshotsError, fetchScreenshots,
      fetchChatList, startNewChat, updateChat, fetchMoreChats, fetchMessages, fetchMoreMessages,
      refreshChatListContext, refreshMessagesContext,
      // WebSocket Hook State (use correct destructured names)
      isConnected, connectionError, parseError, sendingMessage, sendMessageError, 
      // Context Actions / Hook Wrappers
      selectChat, sendMessage, setCurrentMessageText, setSelectedChatId,
      fetchMoreChatsContext, fetchMessagesContext, fetchMoreMessagesContext,
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
