import { apiClient } from '@/api/client'
import { ApiResponse } from '@/api/types/api.types'

import { 
  ChatListItem, 
  Chat, 
  Message, 
  CreateChatPayload, 
  CreateMessagePayload 
} from '@/api/types/chat.types'

// === Chat Endpoints ===

const CHAT_API_PREFIX = '/chats'; // Matches backend router prefix

/**
 * Fetches the list of chats for the current user.
 */
export const getChats = (
  options?: RequestInit & { signal?: AbortSignal } 
): Promise<ApiResponse<ChatListItem[]>> => {
  return apiClient.get<ChatListItem[]>(`${CHAT_API_PREFIX}/`, options);
};

/**
 * Fetches the details (including messages) for a specific chat.
 */
export const getChatDetails = (
  chatId: string,
  options?: RequestInit & { signal?: AbortSignal }
): Promise<ApiResponse<Chat>> => {
  return apiClient.get<Chat>(`${CHAT_API_PREFIX}/${chatId}`, options);
};

/**
 * Creates a new chat session.
 */
export const createChat = (
  payload: CreateChatPayload,
  options?: RequestInit & { signal?: AbortSignal }
): Promise<ApiResponse<Chat>> => {
  return apiClient.post<Chat>(`${CHAT_API_PREFIX}/`, payload, options);
};

/**
 * Adds a message to a specific chat session.
 */
export const addMessage = (
  chatId: string,
  payload: CreateMessagePayload,
  options?: RequestInit & { signal?: AbortSignal }
): Promise<ApiResponse<Message>> => {
  return apiClient.post<Message>(`${CHAT_API_PREFIX}/${chatId}/messages`, payload, options);
};