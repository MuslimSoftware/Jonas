import { apiClient as api } from '@/api/client'
import { ApiResponse } from '@/api/types/api.types'

import { 
  Chat, 
  Message, 
  CreateChatPayload, 
  ChatUpdatePayload,
  CreateMessagePayload,
  PaginationParams,
  PaginatedResponseData,
  GetChatsResponse,
  GetChatDetailsResponse,
  GetChatMessagesResponse,
  CreateChatResponse,
  AddMessageResponse
} from '../types/chat.types'

// === Chat Endpoints ===

// Type hints for the actual data returned by the API calls
// (useful for useApi hook generics)
export type GetChatsData = PaginatedResponseData<Chat>
export type GetChatDetailsData = Chat
export type CreateChatData = Chat
export type AddMessageData = Message
export type GetChatMessagesData = PaginatedResponseData<Message>
export type UpdateChatData = Chat

// Helper to build query string safely
const buildQueryString = (params?: PaginationParams): string => {
    if (!params) return '';
    const query = new URLSearchParams();
    if (params.limit !== undefined) {
        query.append('limit', String(params.limit));
    }
    if (params.before_timestamp) {
        query.append('before_timestamp', params.before_timestamp);
    }
    const queryString = query.toString();
    return queryString ? `?${queryString}` : '';
};

const CHAT_API_PREFIX = '/chats'; // Matches backend router prefix

/**
 * Fetches a paginated list of chats for the user.
 */
export const getChats = async (params?: PaginationParams): Promise<GetChatsResponse> => {
  const queryString = buildQueryString(params);
  // Pass the inner data type to the generic
  return api.get<GetChatsData>(`${CHAT_API_PREFIX}/${queryString}`);
}

/**
 * Fetches the details of a specific chat (excluding messages).
 */
export const getChatDetails = async (chatId: string): Promise<GetChatDetailsResponse> => {
  // Pass the inner data type to the generic
  return api.get<GetChatDetailsData>(`${CHAT_API_PREFIX}/${chatId}`);
}

/**
 * Fetches a paginated list of messages for a specific chat.
 */
export const getChatMessages = async (chatId: string, params?: PaginationParams): Promise<GetChatMessagesResponse> => {
  const queryString = buildQueryString(params);
  // Pass the inner data type to the generic
  return api.get<GetChatMessagesData>(`${CHAT_API_PREFIX}/${chatId}/messages${queryString}`);
}

/**
 * Creates a new chat.
 */
export const createChat = async (payload: CreateChatPayload): Promise<CreateChatResponse> => {
  // Pass the inner data type to the generic
  return api.post<CreateChatData>(`${CHAT_API_PREFIX}/`, payload);
}

/**
 * Updates a chat's name and/or subtitle.
 */
export const updateChat = async (chatId: string, payload: ChatUpdatePayload): Promise<GetChatDetailsResponse> => { 
    return api.patch<UpdateChatData>(`${CHAT_API_PREFIX}/${chatId}`, payload);
}

/**
 * Adds a message to a specific chat.
 * Note: This REST endpoint exists alongside the WebSocket for potentially different use cases
 * or as a fallback, though primary message sending might use WS.
 */
export const addChatMessage = async (chatId: string, payload: CreateMessagePayload): Promise<AddMessageResponse> => {
  // Pass the inner data type to the generic
  return api.post<AddMessageData>(`${CHAT_API_PREFIX}/${chatId}/messages`, payload);
}