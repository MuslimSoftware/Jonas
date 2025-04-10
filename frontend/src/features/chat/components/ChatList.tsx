import React from 'react';
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
import { ChatListItem } from '@/api/types/chat.types';

export const ChatList: React.FC = () => {
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

  const renderChatItem = ({ item }: { item: ChatListItem }) => (
    <Pressable 
      key={item._id}
      style={[
        styles.chatListItem,
        item._id === selectedChatId && styles.chatListItemSelected
      ]}
      onPress={() => selectChat(item._id)}
    >
      <TextBody numberOfLines={1} style={styles.chatListName}>
        {item.name || 'Chat'}
      </TextBody>
    </Pressable>
  );

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
  chatListName: {
    fontWeight: 'bold',
  },
  loadingMoreContainer: {
    paddingVertical: paddings.medium,
    alignItems: 'center',
  }
}); 