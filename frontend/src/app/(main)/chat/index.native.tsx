import React from 'react';
import { StyleSheet } from 'react-native';
import { BgView } from '@/features/shared/components/layout';
import { ChatList } from '@/features/chat/components/ChatList';

export default function NativeChatListScreen() {
  return (
    <BgView style={styles.container}>
      <ChatList />
    </BgView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  }
}); 