import { ChatListItem, Message } from '@/api/types/chat.types';
import { ApiError } from '@/api/types/api.types';

export interface ChatState {
  chatList: ChatListItem[] | null;
  messages: Message[] | null;
  selectedChatId: string | null;
  currentMessage: string;
  loadingChats: boolean;
  loadingMessages: boolean;
  sendingMessage: boolean;
  creatingChat: boolean;
  chatsError: ApiError | null;
  messagesError: ApiError | null;
  sendMessageError: ApiError | null;
  createChatError: ApiError | null;
  isWsConnected: boolean;
}

export interface ChatContextType extends ChatState {
  selectChat: (id: string) => void;
  sendMessage: () => Promise<void>;
  setCurrentMessageText: (text: string) => void;
  startNewChat: () => Promise<void>;
  fetchChatList: () => void;
  setSelectedChatId: (id: string | null) => void;
}