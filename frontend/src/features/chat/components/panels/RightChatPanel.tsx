import React, { useEffect } from 'react';
import { StyleSheet, Pressable, ScrollView, Image, View, Dimensions, ActivityIndicator, Text } from 'react-native';
import { BgView, BaseColumn } from '@/features/shared/components/layout';
import { paddings, borderRadii } from '@/features/shared/theme/spacing';
import { useTheme } from '@/features/shared/context/ThemeContext';
import { useChat } from '../../context';
import { Ionicons } from '@expo/vector-icons';
import { iconSizes } from '@/features/shared/theme/sizes';
import Animated, { 
  useSharedValue, 
  useAnimatedStyle, 
  withTiming, 
  Easing 
} from 'react-native-reanimated';
import { Theme } from '@/features/shared/context/ThemeContext';

interface RightChatPanelProps {
  isVisible: boolean;
  onClose: () => void;
}

const PANEL_WIDTH_PERCENT = 30;
const ANIMATION_DURATION = 250;

export const RightChatPanel: React.FC<RightChatPanelProps> = ({
  isVisible,
  onClose,
}) => {
  const { theme } = useTheme();
  const { 
    screenshots, 
    loadingScreenshots, 
    screenshotsError, 
    fetchScreenshots, 
    selectedChatId // Need chat ID to fetch
  } = useChat();
  const animatedWidth = useSharedValue(isVisible ? PANEL_WIDTH_PERCENT : 0);

  // Trigger animation when isVisible changes
  useEffect(() => {
    animatedWidth.value = withTiming(
      isVisible ? PANEL_WIDTH_PERCENT : 0,
      { duration: ANIMATION_DURATION, easing: Easing.inOut(Easing.ease) }
    );
    // Fetch screenshots when panel becomes visible and we have a chat ID
    if (isVisible && selectedChatId) {
      fetchScreenshots(selectedChatId);
    }
  }, [isVisible, animatedWidth, selectedChatId, fetchScreenshots]);

  // Animated style for the container
  const animatedStyle = useAnimatedStyle(() => {
    const marginRightValue = isVisible ? paddings.medium : 0;
    return {
      width: `${animatedWidth.value}%`,
      marginRight: withTiming(marginRightValue, { duration: ANIMATION_DURATION, easing: Easing.inOut(Easing.ease) }),
      overflow: 'hidden',
    };
  });

  if (!isVisible && animatedWidth.value === 0) {
     return null;
  }

  // Get styles using the theme
  const styles = getStyles(theme);

  return (
    <Animated.View style={[styles.animatedContainer, animatedStyle]}>
      <BgView style={styles.rightPanelContent}>
        <Pressable style={styles.closeRightPanelButton} onPress={onClose}>
          <Ionicons name="close-outline" size={iconSizes.medium} color={theme.colors.text.secondary} />
        </Pressable>
        <BaseColumn style={styles.panelColumn}>
          <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollViewContent}>
            {/* --- Handle Loading and Error States --- */}
            {loadingScreenshots && <ActivityIndicator color={theme.colors.text.primary} />}
            {screenshotsError && <Text style={styles.errorText}>Error loading screenshots.</Text>}
            {!loadingScreenshots && !screenshotsError && screenshots.map((screenshot) => {
              return (
                <View key={screenshot._id} style={styles.screenshotContainer}>
                  <Image 
                    source={{ uri: screenshot.image_data }}
                    style={styles.screenshotImage}
                    resizeMode="contain"
                  />
                </View>
              );
            })}
            {!loadingScreenshots && !screenshotsError && screenshots.length === 0 && (
              <Text style={styles.emptyText}>No agent screenshots available.</Text>
            )}
          </ScrollView>
        </BaseColumn>
      </BgView>
    </Animated.View>
  );
};

// Convert styles to a function accepting theme
const getStyles = (theme: Theme) => StyleSheet.create({
  animatedContainer: {
    height: '97.5%',
    borderRadius: borderRadii.large,
    overflow: 'hidden',
  },
  rightPanelContent: {
    height: '100%',
    paddingTop: paddings.xlarge, 
    paddingBottom: paddings.medium,
    paddingHorizontal: paddings.medium,
    position: 'relative',
  },
  closeRightPanelButton: {
    position: 'absolute',
    top: paddings.medium, 
    right: paddings.medium, 
    zIndex: 1,
  },
  panelColumn: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  scrollViewContent: {
    alignItems: 'center',
    paddingVertical: paddings.medium, 
  },
  screenshotContainer: {
    marginBottom: paddings.medium, 
    borderWidth: 1,
    borderColor: theme.colors.layout.border,
    borderRadius: borderRadii.medium,
    overflow: 'hidden',
    width: '95%',
  },
  screenshotImage: {
    width: '100%', 
    aspectRatio: 16 / 9, // Adjust aspect ratio if known, otherwise use height
    // height: 200, // Or set a fixed height
  },
  errorText: {
    color: theme.colors.indicators.error,
    marginTop: paddings.medium,
  },
  emptyText: {
    color: theme.colors.text.secondary,
    marginTop: paddings.medium,
  },
}); 