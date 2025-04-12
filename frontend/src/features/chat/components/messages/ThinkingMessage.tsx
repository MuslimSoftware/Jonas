import React from 'react';
import { StyleSheet, View, ActivityIndicator } from 'react-native';
import { TextBody } from '@/features/shared/components/text';
import { paddings, gaps } from '@/features/shared/theme/spacing';
import { useTheme } from '@/features/shared/context/ThemeContext';
import { Message } from '@/api/types/chat.types';
import { BaseMessage } from './BaseMessage';

interface ThinkingMessageProps {
  item: Message;
}

export const ThinkingMessage: React.FC<ThinkingMessageProps> = ({ item }) => {
  const { theme } = useTheme();
  return (
    <BaseMessage item={item}>
      <View style={styles.container}>
        <ActivityIndicator size="small" color={theme.colors.text.secondary} />
        <TextBody style={[styles.text, { color: theme.colors.text.secondary }]}>
          Thinking...
        </TextBody>
      </View>
    </BaseMessage>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: gaps.small,
    // BaseMessage handles padding, so internal container might not need extra
  },
  text: {
    fontStyle: 'italic',
  },
}); 