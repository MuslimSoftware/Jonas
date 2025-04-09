import React from 'react';
import {
  StyleSheet,
  View,
} from 'react-native';
import { FgView } from '@/features/shared/components/layout';
import { ChatHeader } from '../ChatHeader';
import { MessageList } from '../MessageList';
import { ChatInput } from '../ChatInput';

interface CenterChatPanelProps {
  isRightPanelVisible: boolean; 
  onToggleRightPanel: () => void; 
}

export const CenterChatPanel: React.FC<CenterChatPanelProps> = ({ 
  isRightPanelVisible,
  onToggleRightPanel,
}) => {
  return (
    <View style={styles.centerPanelWrapper}>
      <FgView style={styles.centerPanel}>
        <ChatHeader 
          isRightPanelVisible={isRightPanelVisible}
          onToggleRightPanel={onToggleRightPanel}
        />
        <MessageList />
        <ChatInput />
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