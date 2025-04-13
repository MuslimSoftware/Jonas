import React, { memo } from 'react';
import {
  StyleSheet,
  Pressable,
  View,
  Platform,
} from 'react-native';
import { TextBody, TextSubtitle } from '@/features/shared/components/text';
import { paddings, borderRadii, gaps } from '@/features/shared/theme/spacing';
import { Theme, useTheme } from '@/features/shared/context/ThemeContext';
import { useChat } from '../context';
import { Chat } from '@/api/types/chat.types';
import { formatTimestamp } from '@/features/shared/utils';
import { BaseFlatList } from '@/features/shared/components/layout/lists';

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
      fetchMoreChats,
      refreshChatList,
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
            {item.latest_message_content ? (
                <TextSubtitle color={theme.colors.text.secondary} numberOfLines={1}>
                    {item.latest_message_content}
                </TextSubtitle>
            ) : null}
          </View>

          {formattedTime ? (
            <TextSubtitle color={theme.colors.text.secondary} style={styles.timestamp}>
              {formattedTime}
            </TextSubtitle>
          ) : null}
        </View>
      </Pressable>
    );
  };

  return (
    <BaseFlatList<Chat>
      data={chatListData?.items ?? []}
      isLoading={loadingChats}
      isError={!!chatsError}
      error={chatsError}
      isEmpty={!chatListData?.items || chatListData.items.length === 0}
      emptyStateMessage="No chats yet."
      isLoadingMore={loadingMoreChats}
      onEndReached={fetchMoreChats}
      onRefresh={refreshChatList}
      renderItem={renderChatItem}
      keyExtractor={(item: Chat) => item._id}
      contentContainerStyle={styles.chatListContainer}
      onEndReachedThreshold={0.5}
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
    paddingBottom: paddings.medium,
    ...Platform.select({
      ios: {
        paddingTop: paddings.small,
      },
      android: {
        paddingTop: paddings.small,
      },
    }),
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