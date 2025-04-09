import React, { useState } from 'react';
import {
  StyleSheet,
  Pressable,
} from 'react-native';
import { BaseRow } from '@/features/shared/components/layout';
import { paddings } from '@/features/shared/theme/spacing';
import { useTheme } from '@/features/shared/context/ThemeContext';
import { Ionicons } from '@expo/vector-icons';
import { iconSizes } from '@/features/shared/theme/sizes';
import {
  LeftChatPanel,
  CenterChatPanel,
  RightChatPanel,
} from './components';

const ChatScreen = () => {
  const { theme } = useTheme();
  const [isRightPanelVisible, setIsRightPanelVisible] = useState(false);
  const [isLeftPanelVisible, setIsLeftPanelVisible] = useState(true);

  const toggleRightPanel = () => {
    setIsRightPanelVisible(!isRightPanelVisible);
  };

  const toggleLeftPanel = () => {
    setIsLeftPanelVisible(!isLeftPanelVisible);
  };

  return (
    <BaseRow style={styles.container}>
      {!isLeftPanelVisible && (
        <Pressable style={styles.openLeftPanelButton} onPress={toggleLeftPanel}>
           <Ionicons 
             name="menu-outline" 
             size={iconSizes.medium} 
             color={theme.colors.text.secondary} 
            />
        </Pressable>
      )}

      <LeftChatPanel 
        isVisible={isLeftPanelVisible}
        onClose={toggleLeftPanel}
      />

      <CenterChatPanel 
        isRightPanelVisible={isRightPanelVisible}
        onToggleRightPanel={toggleRightPanel}
      />

      <RightChatPanel 
        isVisible={isRightPanelVisible}
        onClose={toggleRightPanel}
      />
    </BaseRow>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    position: 'relative',
  },
  openLeftPanelButton: {
    position: 'absolute',
    top: paddings.medium,
    left: paddings.medium,
    zIndex: 10,
  },
});

export default ChatScreen;
