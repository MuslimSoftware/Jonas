import React from 'react';
import {
  View,
  StyleSheet,
  Pressable,
  PressableProps,
  StyleProp,
  ViewStyle,
  Platform,
} from 'react-native';
import {
  Ionicons,
} from '@expo/vector-icons';
import { TextBody } from '../text';
import { Theme, useTheme } from '../../theme';

type IconName = keyof typeof Ionicons.glyphMap;

export interface ListButtonProps extends PressableProps {
  label: string;
  icon?: IconName;
  style?: StyleProp<ViewStyle>;
  showChevron?: boolean;
  iconColor?: string;
  labelColor?: string;
  chevronColor?: string;
}

export const ListButton = React.forwardRef<View, ListButtonProps>((
  { 
    label,
    icon,
    style,
    onPress,
    showChevron = true,
    iconColor,
    labelColor,
    chevronColor,
    ...props 
  },
  ref
) => {
  const { theme } = useTheme();
  const finalIconColor = iconColor || theme.colors.text.primary;
  const finalLabelColor = labelColor || theme.colors.text.primary;
  const finalChevronColor = chevronColor || theme.colors.text.secondary;
  const styles = createStyles(theme);

  return (
    <Pressable
      ref={ref}
      style={({ pressed }) => [
        styles.container,
        Platform.select({ web: { cursor: 'pointer' } }),
        { opacity: pressed ? 0.7 : 1 },
        style,
      ]}
      onPress={onPress}
      accessibilityRole="button"
      {...props}
    >
      <View style={styles.content}>
        <View style={styles.leftContent}>
          {icon && (
            <Ionicons
              name={icon}
              size={theme.typography.body1.fontSize * 1.2}
              color={finalIconColor}
              style={styles.icon}
            />
          )}
          <TextBody style={[styles.label, { color: finalLabelColor }]}>
            {label}
          </TextBody>
        </View>
        {showChevron && (
          <Ionicons
            name="chevron-forward"
            size={theme.typography.body1.fontSize * 1.2}
            color={finalChevronColor}
          />
        )}
      </View>
    </Pressable>
  );
});

const createStyles = (theme: Theme) => StyleSheet.create({
  container: {
    padding: theme.spacing.list?.item?.padding ?? theme.spacing.button.padding ?? 16,
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  leftContent: {
    flexDirection: 'row',
    alignItems: 'center',
    flexShrink: 1,
    marginRight: theme.spacing.list?.item?.gap ?? theme.spacing.button.gap ?? 8,
  },
  icon: {
    marginRight: theme.spacing.list?.item?.gap ?? theme.spacing.button.gap ?? 8,
    textAlign: 'center',
  },
  label: {
    flexShrink: 1,
  },
});

ListButton.displayName = 'ListButton';

 