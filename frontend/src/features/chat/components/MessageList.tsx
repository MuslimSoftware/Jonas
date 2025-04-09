import React, { useEffect, useRef } from 'react';
import {
  StyleSheet,
  FlatList,
  View,
  ActivityIndicator,
} from 'react-native';
import { TextBody, TextSubtitle } from '@/features/shared/components/text';
import { paddings, borderRadii } from '@/features/shared/theme/spacing';
import { useTheme } from '@/features/shared/context/ThemeContext';
import { useChat } from '../context';
import { Message } from '@/api/types/chat.types';

export const MessageList: React.FC = () => {
  const { theme } = useTheme();
  const {
    messages,
    loadingMessages,
    messagesError,
    isWsConnected,
  } = useChat();
  const flatListRef = useRef<FlatList<Message>>(null);

  useEffect(() => {
    console.log('messages:', messages);
    if (messages && messages.length > 0) {
      const timer = setTimeout(() => {
        flatListRef.current?.scrollToEnd({ animated: true });
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [messages]);

  const renderMessage = ({ item }: { item: Message }) => {
    const isUser = item.sender_type === 'user';
    
    const messageStyle = [
      styles.messageBubble,
      isUser ? styles.userMessage : styles.agentMessage,
      {
        backgroundColor: isUser ? theme.colors.layout.background : theme.colors.layout.foreground,
        borderColor: isUser ? theme.colors.layout.border : 'transparent',
        borderWidth: isUser ? 1 : 0,
      }
    ];
    const textStyle = {
       color: theme.colors.text.primary 
    }

    return (
      <View style={[styles.messageRow, isUser ? styles.userRow : styles.agentRow]}>
        <View style={messageStyle}>
          <TextBody style={textStyle}>{item.content}</TextBody>
        </View>
      </View>
    );
  };

  if (loadingMessages) {
    return (
      <View style={styles.centeredContainer}>
        <ActivityIndicator size="large" color={theme.colors.text.primary} />
      </View>
    );
  }

  if (messagesError) {
    return (
      <View style={styles.centeredContainer}>
        <TextSubtitle color={theme.colors.indicators.error}>Error loading messages:</TextSubtitle>
        <TextBody color={theme.colors.indicators.error}>{messagesError.message}</TextBody>
      </View>
    );
  }

  if (!messages || messages.length === 0) {
    return (
      <View style={styles.centeredContainer}>
        {isWsConnected ? (
           <TextSubtitle color={theme.colors.text.secondary}>Send a message to start chatting!</TextSubtitle>
        ) : (
           <TextSubtitle color={theme.colors.text.secondary}>No messages yet</TextSubtitle>
        )} 
      </View>
    );
  }

  return (
    <FlatList
      ref={flatListRef}
      data={messages}
      renderItem={renderMessage}
      keyExtractor={(item) => item._id}
      style={styles.list}
      contentContainerStyle={styles.listContent}
    />
  );
};

const styles = StyleSheet.create({
  list: {
    flex: 1,
  },
  listContent: {
    padding: paddings.medium,
  },
  centeredContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: paddings.large,
  },
  messageRow: {
    flexDirection: 'row',
    marginBottom: paddings.medium,
  },
  userRow: {
    justifyContent: 'flex-end',
  },
  agentRow: {
    justifyContent: 'flex-start',
  },
  messageBubble: {
    paddingVertical: paddings.small,
    paddingHorizontal: paddings.medium,
    borderRadius: borderRadii.large,
    maxWidth: '80%',
  },
  userMessage: {
  },
  agentMessage: {
  },
}); 