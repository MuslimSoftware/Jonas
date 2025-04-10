import { ChatListItem, Message, PaginatedResponseData } from '@/api/types/chat.types';
import { ApiError } from '@/api/types/api.types';

export interface ChatState {
  chatListData: PaginatedResponseData<ChatListItem> | null;
  messageData: PaginatedResponseData<Message> | null;
  selectedChatId: string | null;
  currentMessage: string;
  loadingChats: boolean;
  loadingMessages: boolean;
  creatingChat: boolean;
  chatsError: ApiError | null;
  messagesError: ApiError | null;
  createChatError: ApiError | null;
  loadingMoreChats: boolean;
  loadingMoreMessages: boolean;
  isWsConnected: boolean;
  wsConnectionError: Event | null;
  wsParseError: Error | null;
  sendingMessage: boolean;
  sendMessageError: ApiError | null;
}

export interface ChatContextType extends ChatState {
  selectChat: (id: string) => void;
  sendMessage: () => Promise<void>;
  setCurrentMessageText: (text: string) => void;
  startNewChat: () => Promise<void>;
  fetchChatList: () => void;
  fetchMoreChats: () => void;
  fetchMessages: (chatId: string) => void;
  fetchMoreMessages: () => void;
  setSelectedChatId: (id: string | null) => void;
}