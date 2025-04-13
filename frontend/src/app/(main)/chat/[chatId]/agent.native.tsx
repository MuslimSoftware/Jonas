import React, { useEffect } from 'react';
import { 
  Pressable, 
  StyleSheet, 
  View, 
  ScrollView, 
  Image, 
  ActivityIndicator, 
  Text // Use basic Text for errors/empty
} from 'react-native';
import { Stack, useLocalSearchParams, useNavigation } from 'expo-router';
import { BgView } from '@/features/shared/components/layout';
import { TextBody } from '@/features/shared/components/text';
import { paddings, borderRadii } from '@/features/shared/theme/spacing';
import { iconSizes } from '@/features/shared/theme/sizes';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '@/features/shared/context/ThemeContext';
import { Theme } from '@/features/shared/context/ThemeContext';
import { useChat } from '@/features/chat/context';

export default function NativeAgentDetailScreen() {
  const { chatId } = useLocalSearchParams<{ chatId: string }>();
  const navigation = useNavigation();
  const { theme } = useTheme();
  const { 
    screenshots, 
    loadingScreenshots, 
    screenshotsError, 
    fetchScreenshots 
  } = useChat();
  
  useEffect(() => {
    if (chatId) {
      fetchScreenshots(chatId);
    }
  }, [chatId, fetchScreenshots]);

  // Define styles *before* the early return
  const styles = getStyles(theme);

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
      {/* --- Screenshot Display Area --- */} 
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollViewContent}>
        {/* Handle Loading and Error States */} 
        {loadingScreenshots && <ActivityIndicator color={theme.colors.text.primary} style={styles.centered} />}
        {screenshotsError && <Text style={styles.errorText}>Error loading agent activity.</Text>}
        {!loadingScreenshots && !screenshotsError && screenshots.map((screenshot) => (
            <View key={screenshot._id} style={styles.screenshotContainer}>
              <Image 
                source={{ uri: screenshot.image_data }}
                style={styles.screenshotImage}
                resizeMode="contain"
              />
            </View>
        ))}
        {!loadingScreenshots && !screenshotsError && screenshots.length === 0 && (
          <Text style={styles.emptyText}>No agent activity recorded yet.</Text>
        )}
      </ScrollView>
      {/* --- End Screenshot Display Area --- */} 
    </BgView>
  );
}

const getStyles = (theme: Theme) => StyleSheet.create({
  container: {
    flex: 1,
  },
  contentContainer: {
      flex: 1,
      padding: paddings.medium,
      alignItems: 'center', 
      justifyContent: 'center',
  },
  centered: {
     marginTop: paddings.large,
  },
  scrollView: {
    flex: 1,
  },
  scrollViewContent: {
    alignItems: 'center',
    paddingVertical: paddings.medium, 
    paddingHorizontal: paddings.medium,
  },
  screenshotContainer: {
    marginBottom: paddings.medium, 
    borderWidth: 1,
    borderColor: theme.colors.layout.border,
    borderRadius: borderRadii.medium,
    overflow: 'hidden',
    width: '100%',
  },
  screenshotImage: {
    width: '100%', 
    aspectRatio: 16 / 9, 
  },
  errorText: {
    color: theme.colors.indicators.error,
    marginTop: paddings.large,
  },
  emptyText: {
    color: theme.colors.text.secondary,
    marginTop: paddings.large,
  }
}); 