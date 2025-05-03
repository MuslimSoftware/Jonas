import { Chat, Message, PaginatedResponseData, ChatUpdatePayload, ScreenshotData, ContextItemData } from '@/api/types/chat.types';
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
  wsConnectionError: string | Event | null;
  wsParseError: Error | null;
  sendingMessage: boolean;
  sendMessageError: ApiError | null;
  updatingChat: boolean;
  updateChatError: ApiError | null;
  screenshots: ScreenshotData[];
  loadingScreenshots: boolean;
  screenshotsError: ApiError | null;
  loadingMoreScreenshots: boolean;
  hasMoreScreenshots: boolean;
  totalScreenshotsCount: number | null;
  contextItems: ContextItemData[];
  loadingContext: boolean;
  contextError: ApiError | null;
  loadingMoreContext: boolean;
  hasMoreContext: boolean;
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
  fetchScreenshots: (chatId: string) => Promise<{ items: ScreenshotData[], total_items: number | null } | null>;
  setSelectedChatId: (id: string | null) => void;
  fetchMoreScreenshots: () => Promise<{ items: ScreenshotData[], total_items: number | null } | null>;
  resetScreenshots: () => void;
  fetchContextItems: (chatId: string) => Promise<void>;
  fetchMoreContextItems: () => Promise<void>;
}