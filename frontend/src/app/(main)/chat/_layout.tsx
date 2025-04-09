import React from 'react';
import { Slot } from 'expo-router';
import { ChatProvider } from '@/features/chat/context';

export default function ChatWebLayout() {
  return (
    <ChatProvider>
      <Slot />
    </ChatProvider>
  );
} 