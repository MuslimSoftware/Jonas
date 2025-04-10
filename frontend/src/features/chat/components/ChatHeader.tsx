import React from 'react';
import { StyleSheet, Pressable, View } from 'react-native';
import { BaseRow, BaseColumn } from '@/features/shared/components/layout';
import { TextBody, TextSubtitle } from '@/features/shared/components/text';
import { paddings, gaps } from '@/features/shared/theme/spacing';
import { useTheme } from '@/features/shared/context/ThemeContext';
import { Ionicons } from '@expo/vector-icons';
import { iconSizes } from '@/features/shared/theme/sizes';
import { useChat } from '../context';

interface ChatHeaderProps {
  isRightPanelVisible: boolean;
  onToggleRightPanel: () => void;
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({
  isRightPanelVisible,
  onToggleRightPanel,
}) => {
  const { theme } = useTheme();
  const { selectedChatId, chatListData } = useChat();
  const selectedChat = chatListData?.items.find(chat => chat._id === selectedChatId);
  const title = selectedChat?.name;
  const subtitle = selectedChat?.subtitle || '-';

  return (
    <BaseRow style={styles.centerHeader}>

      <BaseColumn style={styles.chatTitleContainer}>
        {title && <TextBody style={styles.chatTitle} numberOfLines={1}>{title}</TextBody>}
        <TextSubtitle style={styles.chatSubtitle} color={theme.colors.text.secondary} numberOfLines={1}>
          {subtitle}
        </TextSubtitle>
      </BaseColumn>

      <View style={styles.iconContainerRight}>
        {!isRightPanelVisible && (
          <Pressable style={styles.headerButton} onPress={onToggleRightPanel}>
            <Ionicons name="desktop-outline" size={iconSizes.medium} color={theme.colors.text.secondary} />
          </Pressable>
        )}
      </View>
    </BaseRow>
  );
};

const styles = StyleSheet.create({
  centerHeader: {
    paddingHorizontal: paddings.medium,
    paddingTop: paddings.medium,
    paddingBottom: paddings.small,
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  iconContainerRight: {
      minWidth: iconSizes.medium,
      alignItems: 'flex-end',
      marginLeft: gaps.small,
  },
  headerButton: {
  },
  chatTitleContainer: {
    flex: 1,
    alignItems: 'flex-start',
  },
  chatTitle: {
    fontWeight: 'bold',
  },
  chatSubtitle: {
    marginTop: 2,
  }
}); 