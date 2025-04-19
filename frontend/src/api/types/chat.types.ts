import { ApiResponse } from './api.types';

// --- Pagination Types ---

export interface PaginationParams {
  limit?: number;
  before_timestamp?: string; // ISO 8601 format string for query param
}

export interface PaginatedResponseData<T> {
  items: T[];
  next_cursor_timestamp: string | null; // ISO 8601 format string
  has_more: boolean;
}

// --- Core Data Models ---

export interface Message {
  _id: string;
  sender_type: 'user' | 'agent';
  content: string;
  author_id?: string;
  created_at: string; // ISO 8601 format string
  type: 'text' | 'thinking' | 'tool_use' | 'error' | 'action';
  tool_name?: string;
  isTemporary?: boolean;
  sendError?: boolean;
  isStreaming?: boolean;
}

export interface Chat {
  _id: string;
  name?: string;
  subtitle?: string;
  owner_id: string;
  created_at: string; // ISO 8601 format string
  updated_at: string; // ISO 8601 format string
  latest_message_content?: string;
  latest_message_timestamp?: string;
}

// --- Screenshot Type ---
export interface ScreenshotData {
    _id: string;
    chat_id: string;
    created_at: string; // ISO 8601 format string
    image_data: string; // The full data URI
}

// --- Request Payloads ---

export interface CreateMessagePayload {
  sender_type?: 'user' | 'agent';
  content: string;
}

export interface CreateChatPayload {
  name?: string;
  subtitle?: string;
}

// Add update payload type
export interface ChatUpdatePayload {
    name?: string;
}

// --- API Response Types (Specific Endpoints) ---

export type GetChatsResponse = ApiResponse<PaginatedResponseData<Chat>>;

export type GetChatMessagesResponse = ApiResponse<PaginatedResponseData<Message>>;

// Response for getting *details* of a chat (without messages)
export type GetChatDetailsResponse = ApiResponse<Chat>;

// Response when creating a chat (returns the basic chat details)
export type CreateChatResponse = ApiResponse<Chat>;

// Response when adding a message (returns the created message)
export type AddMessageResponse = ApiResponse<Message>; 