import { Chat, Message, PaginatedResponseData, ChatUpdatePayload } from '@/api/types/chat.types';
import { ApiError } from '@/api/types/api.types';

export interface ChatState {
  chatListData: PaginatedResponseData<Chat> | null;
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
  updatingChat: boolean;
  updateChatError: ApiError | null;
}

export interface ChatContextType extends ChatState {
  selectChat: (id: string) => void;
  sendMessage: () => Promise<void>;
  setCurrentMessageText: (text: string) => void;
  startNewChat: () => Promise<void>;
  updateChat: (chatId: string, payload: ChatUpdatePayload) => Promise<void>;
  fetchChatList: () => void;
  refreshChatList: () => void;
  fetchMoreChats: () => void;
  fetchMessages: (chatId: string) => void;
  fetchMoreMessages: () => void;
  refreshMessages: () => void;
  setSelectedChatId: (id: string | null) => void;
}