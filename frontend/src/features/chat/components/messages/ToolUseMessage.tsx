import React from 'react';
import { StyleSheet, View } from 'react-native';
import { TextBody } from '@/features/shared/components/text';
import { paddings, gaps } from '@/features/shared/theme/spacing';
import { useTheme } from '@/features/shared/context/ThemeContext';
import { Message } from '@/api/types/chat.types';
import { BaseMessage } from './BaseMessage';
import { Ionicons } from '@expo/vector-icons';
import { iconSizes } from '@/features/shared/theme/sizes';

interface ToolUseMessageProps {
  item: Message;
}

export const ToolUseMessage: React.FC<ToolUseMessageProps> = ({ item }) => {
  const { theme } = useTheme();
  const toolName = item.tool_name;

  return (
    <BaseMessage item={item}>
      <View style={styles.container}>
        <Ionicons name="cog-outline" size={iconSizes.small} color={theme.colors.text.secondary} />
        <TextBody style={[styles.text, { color: theme.colors.text.secondary }]}>
          {toolName ? `Using tool: ${toolName}` : 'Using tool...'}
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