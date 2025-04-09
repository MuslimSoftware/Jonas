import React, { useEffect } from 'react';
import { StyleSheet, Pressable } from 'react-native';
import { BgView, BaseColumn } from '@/features/shared/components/layout';
import { paddings, borderRadii } from '@/features/shared/theme/spacing';
import { useTheme } from '@/features/shared/context/ThemeContext';
import { Ionicons } from '@expo/vector-icons';
import { iconSizes } from '@/features/shared/theme/sizes';
import Animated, { 
  useSharedValue, 
  useAnimatedStyle, 
  withTiming, 
  Easing 
} from 'react-native-reanimated';

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
  const animatedWidth = useSharedValue(isVisible ? PANEL_WIDTH_PERCENT : 0);

  // Trigger animation when isVisible changes
  useEffect(() => {
    animatedWidth.value = withTiming(
      isVisible ? PANEL_WIDTH_PERCENT : 0,
      { duration: ANIMATION_DURATION, easing: Easing.inOut(Easing.ease) }
    );
  }, [isVisible, animatedWidth]);

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

  return (
    <Animated.View style={[styles.animatedContainer, animatedStyle]}>
      <BgView style={styles.rightPanelContent}>
        <Pressable style={styles.closeRightPanelButton} onPress={onClose}>
          <Ionicons name="remove-outline" size={iconSizes.medium} color={theme.colors.text.secondary} />
        </Pressable>
        <BaseColumn style={styles.panelColumn}>
          {/* Placeholder for right panel content */}
        </BaseColumn>
      </BgView>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
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
}); 