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
import { paddings, borderRadii } from '@/features/shared/theme/spacing';
import { useTheme } from '@/features/shared/context/ThemeContext';
import { useChat } from '../context';
import { Message } from '@/api/types/chat.types';

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

  // Scroll to bottom (index 0 for inverted list) on new messages or initial load
  useEffect(() => {
    if (messageData?.items && messageData.items.length > 0 && !loadingMoreMessages) {
      // Scroll to index 0 only if not currently prepending older messages
      const timer = setTimeout(() => {
        flatListRef.current?.scrollToIndex({ index: 0, animated: true });
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [messageData?.items, loadingMoreMessages]);

  const renderMessage = useCallback(({ item }: { item: Message }) => {
    const isUser = item.sender_type === 'user';
    
    const messageStyle = [
      styles.messageBubble,
      isUser ? styles.userMessage : styles.agentMessage,
      {
        backgroundColor: isUser ? theme.colors.layout.background : theme.colors.layout.foreground,
        borderColor: isUser ? theme.colors.layout.border : 'transparent',
        borderWidth: isUser ? 1 : 0,
        borderRadius: borderRadii.large, // Consistent border radius
      }
    ];
    const textStyle = {
       color: theme.colors.text.primary 
    }

    return (
      <View key={item._id} style={[styles.messageRow, isUser ? styles.userRow : styles.agentRow]}>
        <View style={messageStyle}>
          <TextBody style={textStyle}>{item.content}</TextBody>
        </View>
      </View>
    );
  }, [theme]);

  const keyExtractor = useCallback((item: Message) => {
    return item._id;
  }, []);

  const handleScroll = (event: NativeSyntheticEvent<NativeScrollEvent>) => {
    const { contentOffset, layoutMeasurement, contentSize } = event.nativeEvent;
    const isScrollAtTop = contentOffset.y <= 50; // Threshold for being near the top
    
    if (isScrollAtTop && !loadingMoreMessages && !blockOnEndReached.current && messageData?.has_more) {
      console.log("Near top, fetching more messages...");
      blockOnEndReached.current = true; // Block fetching until current fetch completes
      fetchMoreMessages();
      // Unblock after a delay to prevent immediate refire on layout changes
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
  if (loadingMessages && !messageData) { // Show only on absolute initial load
    return (
      <View style={styles.centeredContainer}>
        <ActivityIndicator size="large" color={theme.colors.text.primary} />
      </View>
    );
  }

  // Initial error state
  if (messagesError && !messageData) { // Show only if no data loaded yet
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
      data={messageData.items} // Use items from paginated data
      renderItem={renderMessage}
      keyExtractor={keyExtractor}
      style={styles.list}
      contentContainerStyle={styles.listContent}
      inverted // Keep inverted if you prefer new messages at bottom visually
      onScroll={handleScroll} // Use onScroll to detect scrolling to top
      scrollEventThrottle={150} // Adjust frequency of scroll events
      ListHeaderComponent={renderHeader} // Show loader at the top
      // Maintain scroll position is complex, especially with prepending.
      // For simplicity, we accept the jump for now when loading older messages.
      // More advanced solutions might involve calculating scroll offset adjustments.
      extraData={selectedChatId} // Re-render if chat ID changes
    />
  );
});

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
    // borderRadius: borderRadii.large, // Applied in renderMessage
    maxWidth: '80%',
  },
  userMessage: {
  },
  agentMessage: {
  },
  loadingMoreContainer: { // Style for header/footer loading indicator
    paddingVertical: paddings.medium,
    alignItems: 'center',
  }
}); 