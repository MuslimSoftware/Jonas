import React, { useEffect } from 'react';
import { StyleSheet, Pressable } from 'react-native';
import { Stack, useLocalSearchParams, Link } from 'expo-router';
import { FgView } from '@/features/shared/components/layout';
import { MessageList } from '@/features/chat/components/MessageList';
import { ChatInput } from '@/features/chat/components/ChatInput';
import { useChat } from '@/features/chat/context';
import { useTheme } from '@/features/shared/context/ThemeContext';
import { Ionicons } from '@expo/vector-icons';
import { iconSizes } from '@/features/shared/theme/sizes';
import { TextBody } from '@/features/shared/components/text';

export default function NativeChatDetailScreen() {
  const { chatId } = useLocalSearchParams<{ chatId: string }>();
  const { theme } = useTheme();
  const { 
      chatList, 
      setSelectedChatId 
  } = useChat();

  const chatName = chatList.find(chat => chat.id === chatId)?.name || 'Chat';

  useEffect(() => {
    if (chatId) {
      setSelectedChatId(chatId);
    }
  }, [chatId, setSelectedChatId]);

  if (!chatId) {
      return <FgView><TextBody>Error: Chat ID missing</TextBody></FgView>;
  }

  const agentHref = `/chat/${chatId}/agent` as any;

  return (
    <FgView style={styles.container}> 
      <Stack.Screen
        options={{
          title: chatName,
          headerRight: () => (
            <Link href={agentHref} asChild>
              <Pressable>
                <Ionicons 
                  name="desktop-outline" 
                  size={iconSizes.medium} 
                  color={theme.colors.text.secondary} 
                />
              </Pressable>
            </Link>
          ),
        }}
      />
      <MessageList />
      <ChatInput />
    </FgView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
}); 