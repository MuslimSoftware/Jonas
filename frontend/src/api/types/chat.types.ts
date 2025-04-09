
export type MessageData = {
  id: string;
  sender_type: 'user' | 'agent';
  content: string;
  author_id?: string | null;
  created_at: string;
};

export type ChatListItemData = {
  id: string;
  name: string | null;
  owner_id: string;
  created_at: string;
  updated_at: string;
};

export type ChatDetailData = ChatListItemData & {
  messages: MessageData[];
};

export interface CreateChatPayload {
  name?: string | null;
}

export interface CreateMessagePayload {
  sender_type?: 'user' | 'agent';
  content: string;
} 