import React, { memo } from 'react';
import {
  StyleSheet,
  Pressable,
  FlatList,
  View,
  ActivityIndicator,
} from 'react-native';
import { TextBody, TextSubtitle } from '@/features/shared/components/text';
import { paddings, borderRadii, gaps } from '@/features/shared/theme/spacing';
import { Theme, useTheme } from '@/features/shared/context/ThemeContext';
import { useChat } from '../context';
import { Chat } from '@/api/types/chat.types';
import { formatTimestamp } from '@/features/shared/utils';

const ChatListComponent: React.FC = () => {
  const { theme } = useTheme();
  const styles = getStyles(theme);
  const { 
      chatListData,
      selectedChatId, 
      selectChat, 
      loadingChats,
      chatsError,
      loadingMoreChats,
      fetchMoreChats
  } = useChat();

  const renderChatItem = ({ item }: { item: Chat }) => {
    const formattedTime = formatTimestamp(item.latest_message_timestamp);

    return (
      <Pressable 
        key={item._id}
        style={[
          styles.chatListItem,
          item._id === selectedChatId && styles.chatListItemSelected
        ]}
        onPress={() => selectChat(item._id)}
      >
        <View style={styles.chatItemRow}>
          <View style={styles.chatItemContent}>
            <TextBody numberOfLines={1} style={styles.chatListName}>
              {item.name || 'Chat'}
            </TextBody>
            {item.latest_message_content && (
                <TextSubtitle color={theme.colors.text.secondary} numberOfLines={1}>
                    {item.latest_message_content}
                </TextSubtitle>
            )}
          </View>

          {formattedTime && (
            <TextSubtitle color={theme.colors.text.secondary} style={styles.timestamp}>
              {formattedTime}
            </TextSubtitle>
          )}
        </View>
      </Pressable>
    );
  };

  const renderFooter = () => {
    if (!loadingMoreChats) return null;
    return (
      <View style={styles.loadingMoreContainer}>
        <ActivityIndicator size="small" color={theme.colors.text.secondary} />
      </View>
    );
  };

  if (loadingChats && !chatListData) {
    return (
      <View style={styles.centeredContainer}>
        <ActivityIndicator size="large" color={theme.colors.text.primary} />
      </View>
    );
  }

  if (chatsError && !chatListData) {
    return (
      <View style={styles.centeredContainer}>
        <TextSubtitle color={theme.colors.indicators.error}>Error loading chats:</TextSubtitle>
        <TextBody color={theme.colors.indicators.error}>{chatsError.message}</TextBody>
      </View>
    );
  }

  if (!chatListData?.items || chatListData.items.length === 0) {
      return (
          <View style={styles.centeredContainer}>
              <TextSubtitle color={theme.colors.text.secondary}>No chats yet.</TextSubtitle>
          </View>
      );
  }

  return (
    <FlatList
      data={chatListData.items}
      renderItem={renderChatItem}
      keyExtractor={(item) => item._id}
      contentContainerStyle={styles.chatListContainer}
      onEndReached={fetchMoreChats}
      onEndReachedThreshold={0.5}
      ListFooterComponent={renderFooter}
    />
  );
};

export const ChatList = memo(ChatListComponent);

const getStyles = (theme: Theme) => StyleSheet.create({
  centeredContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: paddings.large,
  },
  chatListContainer: {
    paddingTop: paddings.medium,
    paddingBottom: paddings.medium,
  },
  chatListItem: {
    paddingVertical: paddings.small,
    paddingHorizontal: paddings.medium,
    marginBottom: gaps.xsmall,
    borderRadius: borderRadii.medium,
    marginHorizontal: paddings.small,
    borderWidth: 1,
    borderColor: 'transparent',
  },
  chatListItemSelected: {
    backgroundColor: theme.colors.layout.foreground,
    borderColor: theme.colors.layout.border,
  },
  chatItemRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-end',
  },
  chatItemContent: {
    flex: 1,
    marginRight: gaps.small,
  },
  chatListName: {
    fontWeight: 'bold',
  },
  timestamp: {
    fontSize: 12,
  },
  loadingMoreContainer: {
    paddingVertical: paddings.medium,
    alignItems: 'center',
  }
}); 