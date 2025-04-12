import React from 'react';
import { StyleSheet, View, ViewStyle } from 'react-native';
import { paddings, borderRadii } from '@/features/shared/theme/spacing';
import { useTheme } from '@/features/shared/context/ThemeContext';
import { Message } from '@/api/types/chat.types';

interface BaseMessageProps {
  item: Message;
  children: React.ReactNode;
}

export const BaseMessage: React.FC<BaseMessageProps> = ({ item, children }) => {
  const { theme } = useTheme();
  const isUser = item.sender_type === 'user';

  const messageRowStyle: ViewStyle[] = [
    styles.messageRow,
    isUser ? styles.userRow : styles.agentRow,
  ];

  const messageBubbleStyle: ViewStyle[] = [
    styles.messageBubbleBase,
    isUser
      ? {
          backgroundColor: theme.colors.layout.background,
          borderColor: theme.colors.layout.border,
          borderWidth: 1,
        }
      : {
          backgroundColor: theme.colors.layout.foreground,
          borderColor: 'transparent',
          borderWidth: 0,
        },
    item.isTemporary && styles.temporaryMessage,
    item.sendError && styles.errorMessageBubble,
  ].filter(Boolean) as ViewStyle[];

  return (
    <View style={messageRowStyle}>
      <View style={messageBubbleStyle}>{children}</View>
    </View>
  );
};

const styles = StyleSheet.create({
  messageRow: {
    flexDirection: 'row',
    marginBottom: paddings.xsmall, // Add spacing between messages
  },
  userRow: {
    justifyContent: 'flex-end',
  },
  agentRow: {
    justifyContent: 'flex-start',
  },
  messageBubbleBase: {
    paddingVertical: paddings.small,
    paddingHorizontal: paddings.medium,
    borderRadius: borderRadii.large,
    maxWidth: '80%',
    position: 'relative', // For potential absolute positioned elements like error icons
  },
  temporaryMessage: {
    opacity: 0.7, // Example style for temporary messages
  },
  errorMessageBubble: {
    // Add specific styles if needed, maybe border handled by error icon presence
  },
}); 