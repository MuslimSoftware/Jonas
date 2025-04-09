import React from 'react';
import { StyleSheet, Pressable } from 'react-native';
import { Stack } from 'expo-router';
import { BgView } from '@/features/shared/components/layout';
import { ChatList } from '@/features/chat/components/ChatList';
import { AntDesign } from '@expo/vector-icons';
import { useTheme } from '@/features/shared/context/ThemeContext';
import { iconSizes } from '@/features/shared/theme/sizes';
import { paddings } from '@/features/shared/theme/spacing';

export default function NativeChatListScreen() {
  const { theme } = useTheme();

  const handleAddChat = () => {
  };

  return (
    <BgView style={styles.container}>
      <Stack.Screen 
        options={{
          headerRight: () => (
            <Pressable onPress={handleAddChat} style={styles.headerButton}>
              <AntDesign name="plus" size={iconSizes.medium} color={theme.colors.text.primary} />
            </Pressable>
          ),
        }}
      />
      <ChatList />
    </BgView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  headerButton: {
    marginRight: paddings.medium,
  }
}); 