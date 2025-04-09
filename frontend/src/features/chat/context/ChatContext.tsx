import React, { createContext, useState, useContext, ReactNode, useMemo } from 'react';
import { ChatContextType, ChatState, ChatListItemData, MessageData } from './ChatContext.types';
import { Platform } from 'react-native';
import { useRouter } from 'expo-router';

// Define Param List (should ideally be shared/imported)
type RootStackParamList = {
  ChatList: undefined;
  ChatDetail: { chatId: string; chatName: string };
  AgentDetail: { chatId: string };
};

const dummyChatList: ChatListItemData[] = [
  { id: '1', name: 'General Conversation', lastMessage: 'Sounds good!' },
  { id: '2', name: 'Project Alpha', lastMessage: 'Meeting at 3 PM.' },
  { id: '3', name: 'Bug Report', lastMessage: 'Can you check this?' },
];

const dummyMessages: MessageData[] = [
  { id: 'm1', text: 'Hello there!', sender: 'other' },
  { id: 'm2', text: 'Hi! How are you?', sender: 'user' },
  { id: 'm3', text: 'Doing well, thanks! Working on the new UI.', sender: 'other' },
  { id: 'm4', text: 'Nice! How\'s it going?', sender: 'user' },
];

const ChatContext = createContext<ChatContextType | null>(null);

interface ChatProviderProps {
  children: ReactNode;
}

export const ChatProvider: React.FC<ChatProviderProps> = ({ children }) => {
  const [chatList, setChatList] = useState<ChatListItemData[]>(dummyChatList);
  const [messages, setMessages] = useState<MessageData[]>(dummyMessages);
  const [selectedChatId, setSelectedChatId] = useState<string | null>(dummyChatList[0]?.id || null);
  const [currentMessage, setCurrentMessageText] = useState<string>('');
  const router = useRouter();
    
  const selectChat = (id: string) => {
    if (Platform.OS === 'web') {
      setSelectedChatId(id);
    } else {
      router.push(`/chat/${id}` as any);
    }
  };

  const sendMessage = () => {
    if (currentMessage.trim() === '' || !selectedChatId) return;
    const newMessage: MessageData = {
      id: `m${messages.length + 1}`,
      text: currentMessage.trim(),
      sender: 'user',
    };
    setMessages(prevMessages => [...prevMessages, newMessage]);
    setCurrentMessageText('');
  };

  const startNewChat = () => {
      if (Platform.OS === 'web') {
          setSelectedChatId(null);
          setMessages([]);
      } else {
      }
      console.log("Starting new chat...");
  };

  const value = useMemo(() => ({
    chatList,
    messages,
    selectedChatId,
    currentMessage,
    selectChat,
    sendMessage,
    setCurrentMessageText,
    startNewChat,
    setSelectedChatId
  }), [chatList, messages, selectedChatId, currentMessage]);

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
