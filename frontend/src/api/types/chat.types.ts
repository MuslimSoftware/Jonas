
export type Message = {
  _id: string;
  sender_type: 'user' | 'agent';
  content: string;
  authorid?: string | null;
  created_at: string;
};

export type ChatListItem = {
  _id: string;
  name: string | null;
  ownerid: string;
  created_at: string;
  updated_at: string;
};

export type Chat = ChatListItem & {
  messages: Message[];
};

export interface CreateChatPayload {
  name?: string | null;
}

export interface CreateMessagePayload {
  sender_type?: 'user' | 'agent';
  content: string;
} 