import React from 'react';
import { StyleSheet, View } from 'react-native';
import { Stack, useLocalSearchParams } from 'expo-router';
import { BgView } from '@/features/shared/components/layout';
import { TextBody } from '@/features/shared/components/text';
import { paddings } from '@/features/shared/theme/spacing';

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

  if (!chatId) {
    // Handle case where chatId might be missing
    return <BgView style={styles.container}><TextBody>Error: Chat ID missing.</TextBody></BgView>;
  }

  return (
    <BgView style={styles.container}>
      <Stack.Screen
        options={{
          title: 'Agent Task', 
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