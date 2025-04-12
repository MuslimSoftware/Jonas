import React from 'react';
import { StyleSheet, Platform } from 'react-native';
import MarkdownDisplay from 'react-native-markdown-display';
import { useTheme } from '@/features/shared/context/ThemeContext';
import { Message } from '@/api/types/chat.types';
import { BaseMessage } from './BaseMessage';
import { typography } from '@/features/shared/theme';

interface TextMessageProps {
  item: Message;
}

export const TextMessage: React.FC<TextMessageProps> = ({ item }) => {
  const { theme } = useTheme();

  // Define markdown styles based on the theme
  const markdownStyle = StyleSheet.create({
    body: { // Default text style
      fontSize: typography.body1.fontSize,
      color: theme.colors.text.primary,
    },
    heading1: { 
      fontSize: typography.h1.fontSize, 
      color: theme.colors.text.primary, 
      fontWeight: 'bold',
      marginTop: 10, 
      marginBottom: 5,
    },
    heading2: { 
      fontSize: typography.h2.fontSize, 
      color: theme.colors.text.primary, 
      fontWeight: 'bold',
      marginTop: 8, 
      marginBottom: 4,
    },
    // Add styles for other markdown elements (list, code, blockquote, etc.) as needed
    bullet_list: {
      marginBottom: 5,
    },
    ordered_list: {
      marginBottom: 5,
    },
    list_item: {
      flexDirection: 'row',
      alignItems: 'flex-start',
      marginBottom: 2,
    },
    code_inline: { // Inline code
      backgroundColor: theme.colors.layout.foreground, // Slightly different bg
      fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace', // Use monospace font
      paddingHorizontal: 4,
      borderRadius: 3,
      color: theme.colors.text.secondary, // Different color for code
    },
    code_block: { // Fenced code block
      backgroundColor: theme.colors.layout.foreground, // Use foreground as fallback
      padding: 10,
      borderRadius: 4,
      fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace', // Use monospace font
      color: theme.colors.text.primary,
      marginBottom: 10,
    },
    blockquote: {
      backgroundColor: theme.colors.layout.foreground,
      paddingLeft: 10,
      marginLeft: 5,
      borderLeftColor: theme.colors.layout.border,
      borderLeftWidth: 3,
      marginBottom: 10,
    },
    link: {
        color: theme.colors.text.primary,
        textDecorationLine: 'underline',
    },
  });

  return (
    <BaseMessage item={item}>
      <MarkdownDisplay style={markdownStyle}>
        {item.content + (item.isStreaming ? '...' : '')}
      </MarkdownDisplay>
    </BaseMessage>
  );
}; 