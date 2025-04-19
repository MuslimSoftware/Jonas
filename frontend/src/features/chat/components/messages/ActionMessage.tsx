import React from 'react';
import { StyleSheet } from 'react-native';
import { Message } from '@/api/types/chat.types';
import { BaseMessage } from './BaseMessage';
import { TextBody } from '@/features/shared/components/text';
import { useTheme } from '@/features/shared/context/ThemeContext';

interface ActionMessageProps {
  item: Message;
}

export const ActionMessage: React.FC<ActionMessageProps> = ({ item }) => {
  const { theme } = useTheme();

  return (
    <BaseMessage 
      item={item}
      containerStyle={styles.container} // Apply specific style if needed
    >
      <TextBody 
        style={styles.text}
        color={theme.colors.text.secondary} // Use a distinct color, e.g., secondary
      >
        {item.content} 
      </TextBody>
    </BaseMessage>
  );
};

const styles = StyleSheet.create({
  container: {
    // Add specific styling for the action message container if desired
    // e.g., alignSelf: 'center', marginVertical: paddings.small 
  },
  text: {
    fontStyle: 'italic', // Example: make action text italic
    textAlign: 'center', // Example: center the action text
  },
}); 