import React, { useEffect, useRef, useCallback, memo, useState } from 'react';
import {
  StyleSheet,
  FlatList,
  View,
  ActivityIndicator,
  NativeSyntheticEvent,
  NativeScrollEvent,
} from 'react-native';
import { TextBody, TextSubtitle } from '@/features/shared/components/text';
import { paddings, gaps } from '@/features/shared/theme/spacing';
import { useTheme } from '@/features/shared/context/ThemeContext';
import { useChat } from '../context';
import { Message } from '@/api/types/chat.types';
import { TextMessage, ThinkingMessage, ToolUseMessage, ErrorMessage } from './messages';

export const MessageList: React.FC = memo(() => {
  const { theme } = useTheme();
  const {
    messageData,        // Updated: Use paginated data
    loadingMessages,    // Initial load
    messagesError,      // Initial error
    loadingMoreMessages, // Loading older messages state
    fetchMoreMessages,   // Action to load older messages
    isWsConnected,      // To adjust empty state message
    selectedChatId,     // For FlatList extraData
  } = useChat();
  const flatListRef = useRef<FlatList<Message>>(null);
  const [isNearTop, setIsNearTop] = useState(false);
  const blockOnEndReached = useRef(false); // Prevent rapid firing of fetchMore

  useEffect(() => {
    if (messageData?.items && messageData.items.length > 0 && !loadingMoreMessages) {
      const timer = setTimeout(() => {
        flatListRef.current?.scrollToIndex({ index: 0, animated: true });
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [messageData?.items, loadingMoreMessages]);

  const renderMessage = useCallback(({ item }: { item: Message }) => {
    switch (item.type) {
      case 'text':
        return <TextMessage key={item._id} item={item} />;
      case 'thinking':
        return <ThinkingMessage key={item._id || `thinking-${item.created_at}`} item={item} />;
      case 'tool_use':
        return <ToolUseMessage key={item._id || `tool-${item.tool_name}-${item.created_at}`} item={item} />;
      case 'error':
        return <ErrorMessage key={item._id || `error-${item.created_at}`} item={item} />;
      default:
        console.warn("Unhandled message type in MessageList:", item.type);
        return null;
    }
  }, [theme, selectedChatId]);

  // Update keyExtractor to be more robust for potentially missing/temporary IDs
  const keyExtractor = useCallback((item: Message) => {
    return item._id || `${item.sender_type}-${item.type}-${item.created_at}`;
  }, []);

  const handleScroll = (event: NativeSyntheticEvent<NativeScrollEvent>) => {
    const { contentOffset, layoutMeasurement, contentSize } = event.nativeEvent;
    const isScrollAtTop = contentOffset.y <= 50; // Threshold for being near the top
    
    if (isScrollAtTop && !loadingMoreMessages && !blockOnEndReached.current && messageData?.has_more) {
      console.log("Near top, fetching more messages...");
      blockOnEndReached.current = true;
      fetchMoreMessages();
      setTimeout(() => { blockOnEndReached.current = false; }, 1000);
    }
    setIsNearTop(isScrollAtTop);
  };

  const renderHeader = () => {
    if (!loadingMoreMessages) return null;
    return (
      <View style={styles.loadingMoreContainer}>
        <ActivityIndicator size="small" color={theme.colors.text.secondary} />
      </View>
    );
  };

  // Initial loading state
  if (loadingMessages && !messageData) {
    return (
      <View style={styles.centeredContainer}>
        <ActivityIndicator size="large" color={theme.colors.text.primary} />
      </View>
    );
  }

  // Initial error state
  if (messagesError && !messageData) {
    return (
      <View style={styles.centeredContainer}>
        <TextSubtitle color={theme.colors.indicators.error}>Error loading messages:</TextSubtitle>
        <TextBody color={theme.colors.indicators.error}>{messagesError.message}</TextBody>
      </View>
    );
  }

  // Empty state
  if (!messageData?.items || messageData.items.length === 0) {
    return (
      <View style={styles.centeredContainer}>
        {selectedChatId ? (
           <TextSubtitle color={theme.colors.text.secondary}>Send a message to start chatting!</TextSubtitle>
        ) : (
           <TextSubtitle color={theme.colors.text.secondary}>Select a chat to view messages</TextSubtitle>
        )} 
      </View>
    );
  }

  return (
    <FlatList
      ref={flatListRef}
      data={messageData.items}
      renderItem={renderMessage}
      keyExtractor={keyExtractor}
      style={styles.list}
      contentContainerStyle={styles.listContent}
      inverted
      // onScroll={handleScroll}
      // scrollEventThrottle={150}
      ListHeaderComponent={renderHeader}
      // extraData={selectedChatId}
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
  loadingMoreContainer: {
    paddingVertical: paddings.medium,
    alignItems: 'center',
  }
}); 