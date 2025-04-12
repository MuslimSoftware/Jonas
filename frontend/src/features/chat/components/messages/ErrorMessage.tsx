import React from 'react';
import { StyleSheet, View } from 'react-native';
import { TextBody } from '@/features/shared/components/text';
import { paddings, gaps } from '@/features/shared/theme/spacing';
import { useTheme } from '@/features/shared/context/ThemeContext';
import { Message } from '@/api/types/chat.types';
import { BaseMessage } from './BaseMessage';
import { Ionicons } from '@expo/vector-icons';
import { iconSizes } from '@/features/shared/theme/sizes';

interface ErrorMessageProps {
  item: Message;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({ item }) => {
  const { theme } = useTheme();
  const content = item.content;

  return (
    <BaseMessage item={item}>
      <View style={styles.container}>
        <Ionicons name="warning-outline" size={iconSizes.small} color={theme.colors.indicators.error} />
        <TextBody style={[styles.text, { color: theme.colors.indicators.error }]}>
          {content || 'An error occurred.'}
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
  },
  text: {
    fontStyle: 'italic',
  },
}); 