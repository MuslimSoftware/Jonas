import React from 'react';
import {
  StyleSheet,
  Pressable,
  FlatList,
} from 'react-native';
import { TextBody } from '@/features/shared/components/text';
import { paddings, borderRadii, gaps } from '@/features/shared/theme/spacing';
import { useTheme } from '@/features/shared/context/ThemeContext';
import { useChat } from '../context';
import { ChatListItemData } from '../context';

interface ChatListProps {

}

export const ChatList: React.FC<ChatListProps> = ({ /* No props needed */ }) => {
  const { theme } = useTheme();
  const { chatList, selectedChatId, selectChat } = useChat();

  const renderChatItem = ({ item }: { item: ChatListItemData }) => (
    <Pressable 
      style={[
        styles.chatListItem,
        item.id === selectedChatId && styles.chatListItemSelected
      ]}
      onPress={() => selectChat(item.id)}
    >
      <TextBody numberOfLines={1} style={styles.chatListName}>
        {item.name}
      </TextBody>
      <TextBody 
        numberOfLines={1} 
        style={styles.chatListMessage} 
        color={theme.colors.text.secondary}
      >
        {item.lastMessage}
      </TextBody>
    </Pressable>
  );

  return (
    <FlatList
      data={chatList}
      renderItem={renderChatItem}
      keyExtractor={(item) => item.id}
      contentContainerStyle={styles.chatListContainer}
    />
  );
};

const styles = StyleSheet.create({
  chatListContainer: {
    paddingBottom: paddings.medium,
    paddingTop: paddings.medium,
  },
  chatListItem: {
    paddingVertical: paddings.small,
    paddingHorizontal: paddings.medium,
    marginBottom: gaps.xsmall,
    borderRadius: borderRadii.medium,
    marginHorizontal: paddings.small,
  },
  chatListItemSelected: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)', // Consider theme color?
  },
  chatListName: {
    fontWeight: 'bold',
    marginBottom: gaps.xxsmall,
  },
  chatListMessage: {
    fontSize: 12,
  },
}); 