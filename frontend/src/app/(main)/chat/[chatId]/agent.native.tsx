import React from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import { Stack, useLocalSearchParams, useNavigation } from 'expo-router';
import { BgView } from '@/features/shared/components/layout';
import { TextBody } from '@/features/shared/components/text';
import { paddings } from '@/features/shared/theme/spacing';
import { iconSizes } from '@/features/shared/theme/sizes';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '@/features/shared/context/ThemeContext';

// Placeholder component for agent details
const AgentDetailContent: React.FC<{ chatId: string }> = ({ chatId }) => {
  return (
    <View style={styles.contentContainer}>
      <TextBody>Agent details for Chat ID: {chatId}</TextBody>
      {/* Add agent-specific UI components here */}
    </View>
  );
};

export default function NativeAgentDetailScreen() {
  const { chatId } = useLocalSearchParams<{ chatId: string }>();
  const navigation = useNavigation();
  const { theme } = useTheme();
  
  if (!chatId) {
    // Handle case where chatId might be missing
    return <BgView style={styles.container}><TextBody>Error: Chat ID missing.</TextBody></BgView>;
  }

  return (
    <BgView style={styles.container}>
      <Stack.Screen
        options={{
          title: 'Agent Task', 
          headerLeft: () => (
            <Pressable 
              onPress={() => navigation.goBack()}
            >
              <Ionicons 
                name="chevron-back-outline"
                size={iconSizes.medium}
                color={theme.colors.text.primary}
              />
            </Pressable>
          ),
        }}
       
      />
      <AgentDetailContent chatId={chatId} />
    </BgView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  contentContainer: {
      flex: 1,
      padding: paddings.medium,
      alignItems: 'center', 
      justifyContent: 'center',
  }
}); 