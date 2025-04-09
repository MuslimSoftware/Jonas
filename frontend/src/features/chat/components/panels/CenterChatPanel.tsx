import React from 'react';
import {
  StyleSheet,
  View,
} from 'react-native';
import { FgView } from '@/features/shared/components/layout';
import { ChatHeader } from '../ChatHeader';
import { MessageList } from '../MessageList';
import { ChatInput } from '../ChatInput';
import { useChat } from '../../context'; // Import useChat

// Removed local type definition

interface CenterChatPanelProps {
  isRightPanelVisible: boolean; 
  onToggleRightPanel: () => void; 
}

export const CenterChatPanel: React.FC<CenterChatPanelProps> = ({ 
  isRightPanelVisible,
  onToggleRightPanel,
}) => {
  // Get only needed context values
  const { selectedChatId, chatList, currentMessage, setCurrentMessageText, sendMessage } = useChat();

  const selectedChat = chatList.find(chat => chat.id === selectedChatId);

  const headerProps = {
    isRightPanelVisible: isRightPanelVisible,
    onToggleRightPanel: onToggleRightPanel,
  };

  const inputProps = {
      currentMessage: currentMessage,
      setCurrentMessage: setCurrentMessageText,
      onSendMessage: sendMessage,
  };

  return (
    <View style={styles.centerPanelWrapper}>
      <FgView style={styles.centerPanel}>
        <ChatHeader {...headerProps} />
        <MessageList />
        <ChatInput {...inputProps} />
      </FgView>
    </View>
  );
};

const styles = StyleSheet.create({
  centerPanelWrapper: {
    flex: 1,
    height: '100%',
    alignItems: 'center',
    justifyContent: 'center',
  },
  centerPanel: {
    width: '95%',
    maxWidth: 800,
    height: '100%',
    position: 'relative',
  },
}); 