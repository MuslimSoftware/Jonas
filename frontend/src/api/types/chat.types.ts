import { ApiResponse } from './api.types';

// --- Pagination Types ---

export interface PaginationParams {
  limit?: number;
  before_timestamp?: string; // ISO 8601 format timestamp
  sort?: 'asc' | 'desc'; // Add sort property
}

export interface PaginatedResponseData<T> {
  items: T[];
  next_cursor_timestamp: string | null; // ISO 8601 format string
  has_more: boolean;
  total_items?: number | null;
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
    page_summary: string | null;
    evaluation_previous_goal: string | null;
    memory: string | null;
    next_goal: string | null;
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

// --- Add ContextItemData Type ---
export interface ContextItemData {
  _id: string; // Assuming the backend sends _id
  chat_id: string;
  source_agent: string;
  content_type: string;
  data: Record<string, any>; // Using Record<string, any> for flexibility
  created_at: string;
}

// === Paginated Response Wrapper ===

export type GetChatScreenshotsResponse = ApiResponse<PaginatedResponseData<ScreenshotData>>;

// --- Update GetChatContextResponse Type Alias for Pagination ---
export type GetChatContextData = PaginatedResponseData<ContextItemData>;
export type GetChatContextResponse = ApiResponse<GetChatContextData>; 