export type ChatListItemData = { id: string; name: string; lastMessage: string };

export type MessageData = { 
  id: string; 
  text: string; 
  sender: 'user' | 'other' 
}; 

export interface ChatState {
  chatList: ChatListItemData[];
  messages: MessageData[];
  selectedChatId: string | null;
  currentMessage: string;
}

export interface ChatContextType extends ChatState {
  selectChat: (id: string) => void;
  sendMessage: () => void;
  setCurrentMessageText: (text: string) => void;
  startNewChat: () => void;
}