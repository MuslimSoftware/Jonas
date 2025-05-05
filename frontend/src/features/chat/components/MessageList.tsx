import React, { useEffect, useRef, useCallback, memo, useMemo } from 'react';
import {
  StyleSheet,
  View,
  FlatList as RNFlatlist,
  Text,
  Platform,
} from 'react-native';
import { TextSubtitle } from '@/features/shared/components/text';
import { paddings, gaps } from '@/features/shared/theme/spacing';
import { useTheme } from '@/features/shared/context/ThemeContext';
import { useChat } from '../context';
import { Message } from '@/api/types/chat.types';
import { TextMessage, ThinkingMessage, ToolUseMessage, ErrorMessage, ActionMessage } from './messages';
import { BaseFlatList } from '@/features/shared/components/layout/lists';
import { Brand } from '@/features/shared/components/brand/Brand';

export const MessageList: React.FC = memo(() => {
  const { theme } = useTheme();
  const {
    messageData,
    loadingMessages,    // Initial load
    messagesError,
    loadingMoreMessages, // Use this state
    fetchMoreMessages,   // Use this function
    refreshMessages,     // Get refresh function
    isWsConnected,      // To adjust empty state message
    selectedChatId,     // For FlatList extraData
  } = useChat();
  const flatListRef = useRef<RNFlatlist<Message>>(null);
  const prevItemsRef = useRef<Message[] | undefined>();
  const isWeb = Platform.OS === 'web';

  // Reverse data only for web where inverted is false
  const displayData = useMemo(() => {
    const items = messageData?.items ?? [];
    return isWeb ? [...items].reverse() : items;
  }, [messageData?.items, isWeb]);

  useEffect(() => {
    const currentItems = messageData?.items;
    const prevItems = prevItemsRef.current;
    // Check based on the original data order for consistency
    const hasNewMessage = 
      currentItems && prevItems && currentItems.length > 0 && prevItems.length > 0
        ? currentItems[0]?._id !== prevItems[0]?._id 
        : (currentItems?.length ?? 0) > (prevItems?.length ?? 0); // Fallback for initial load

    if (
        currentItems && 
        currentItems.length > 0 && 
        !loadingMoreMessages && 
        hasNewMessage
    ) {
      const timer = setTimeout(() => {
        if (isWeb) {
            // Scroll to end for non-inverted list
            flatListRef.current?.scrollToEnd({ animated: true });
        } else {
            // Scroll to index 0 for inverted list
            flatListRef.current?.scrollToIndex({ index: 0, animated: true });
        }
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [messageData?.items, loadingMoreMessages, isWeb]);

  // Effect to update the ref *after* render completes
  useEffect(() => {
    // Store the original, non-reversed items order
    prevItemsRef.current = messageData?.items;
  });

  const renderMessage = useCallback(({ item, index }: { item: Message, index: number }) => {
    // Use displayData for rendering, but original messages for logic if needed
    const messages = messageData?.items ?? []; // Original order
    const isAgent = item.sender_type === 'agent';

    // Find the chronologically previous message based on platform
    let prevMessage: Message | undefined;
    if (isWeb) {
      // On web, displayData is reversed. Chronologically previous is index - 1.
      prevMessage = displayData[index - 1];
    } else {
      // On native, data is newest first. Chronologically previous is index + 1.
      prevMessage = messages[index + 1]; 
    }

    const isPrevMessageUserOrStart = !prevMessage || prevMessage.sender_type !== 'agent' || item.type !== 'action';
    // Only show name if it's agent, first in sequence, and a text message
    const showAgentName = isAgent && isPrevMessageUserOrStart && item.type == 'text';

    let messageComponent: React.ReactNode = null;

    switch (item.type) {
      case 'text':
        messageComponent = <TextMessage key={item._id} item={item} />;
        break;
      case 'thinking':
        messageComponent = <ThinkingMessage key={item._id || `thinking-${item.created_at}`} item={item} />;
        break;
      case 'tool_use':
        messageComponent = <ToolUseMessage key={item._id || `tool-${item.tool_name}-${item.created_at}`} item={item} />;
        break;
      case 'action':
        messageComponent = <ActionMessage key={item._id || `action-${item.created_at}`} item={item} />;
        break;
      case 'error':
        messageComponent = <ErrorMessage key={item._id || `error-${item.created_at}`} item={item} />;
        break;
      default:
        console.warn("Unhandled message type in MessageList:", item.type);
        return null;
    }

    // Conditionally wrap the message component with the agent name
    if (showAgentName) {
      return (
        <View>
          <Brand />
          {messageComponent}
        </View>
      );
    }

    return messageComponent;

  }, [theme, selectedChatId, messageData?.items, isWeb, displayData]);

  // Update keyExtractor to use the item from displayData
  const keyExtractor = useCallback((item: Message) => {
    // Key extraction logic should be consistent regardless of order
    return item._id || `${item.sender_type}-${item.type}-${item.created_at}`;
  }, []);

  const handleEndReached = useCallback(() => {
    // Check if we have more messages and are not already loading
    // NOTE: For web (non-inverted), onEndReached fires at the bottom (newest messages).
    // We might need a different approach to load *older* messages on web (e.g., onScroll near top).
    if (!isWeb && messageData?.has_more && !loadingMoreMessages) {
        fetchMoreMessages(); // Only fetch on native for now via onEndReached
    }
  }, [messageData?.has_more, loadingMoreMessages, fetchMoreMessages, isWeb]);

  // Custom Empty State Component for Messages
  const MessageEmptyState = () => (
    <View style={styles.centeredContainer}>
      {selectedChatId ? (
         <TextSubtitle color={theme.colors.text.secondary}>Send a message to start chatting!</TextSubtitle>
      ) : (
         <TextSubtitle color={theme.colors.text.secondary}>Select a chat to view messages</TextSubtitle>
      )} 
    </View>
  );

  return (
    <BaseFlatList<Message>
      ref={flatListRef}
      data={displayData}
      isLoading={loadingMessages}
      isError={!!messagesError}
      error={messagesError}
      isEmpty={!messageData?.items || messageData.items.length === 0}
      EmptyStateComponent={MessageEmptyState}
      isLoadingMore={loadingMoreMessages}
      onEndReached={handleEndReached}
      onRefresh={refreshMessages}
      inverted={!isWeb}
      renderItem={renderMessage}
      keyExtractor={keyExtractor}
      style={styles.list}
      contentContainerStyle={styles.listContent}
      onEndReachedThreshold={0.5}
    />
  );
});

const styles = StyleSheet.create({
  list: {
    flex: 1,
  },
  listContent: {
    padding: paddings.medium,
    gap: gaps.xsmall,
  },
  centeredContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: paddings.large,
  },
  agentName: {
    marginLeft: paddings.small,
    fontSize: 12,
    fontWeight: '500',
  },
}); 