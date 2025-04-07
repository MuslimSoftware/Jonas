import React from 'react';
import {
  Pressable,
  PressableProps,
  StyleSheet,
  StyleProp,
  ViewStyle,
  ColorValue,
  Platform,
  View,
} from 'react-native';
import { Theme, useTheme } from '../../theme';
import { TextButtonLabel, TextAliasProps } from '../text'; 

export type ButtonVariant = 'primary' | 'secondary';

export interface BaseButtonProps extends Omit<PressableProps, 'children' | 'style'> {
  children?: React.ReactNode; // Allow no children if label is provided
  label?: string; // Add optional label prop
  labelProps?: Omit<TextAliasProps, 'theme'>; // Props for label text
  variant?: ButtonVariant;
  disabled?: boolean;
  style?: StyleProp<ViewStyle>; // Accept custom style prop
}

export const BaseButton = React.forwardRef<View, BaseButtonProps>((
  { children, label, labelProps, variant = 'primary', disabled = false, style, ...props },
  ref
) => {
  const { theme } = useTheme(); //
  const effectiveVariant = disabled ? 'disabled' : variant;
  const buttonThemeStyles = theme.colors.button[effectiveVariant];

  const baseButtonStyle: ViewStyle = {
    backgroundColor: buttonThemeStyles.background as ColorValue,
    borderColor: buttonThemeStyles.border as ColorValue,
    paddingVertical: theme.spacing.button.padding,
    paddingHorizontal: theme.spacing.button.padding * 1.5,
    borderRadius: theme.spacing.button.borderRadius,
  };

  return (
    <Pressable
      ref={ref}
      style={({ pressed }) => StyleSheet.flatten([
        styles.base,
        baseButtonStyle,
        { opacity: disabled ? 0.5 : (pressed ? 0.7 : 1) },
        Platform.select({ web: { cursor: disabled ? 'not-allowed' : 'pointer' } }) as any,
        style
      ])}
      disabled={disabled}
      accessibilityRole="button"
      {...props}
    >
      {label ? (
        <TextButtonLabel 
          style={{ color: buttonThemeStyles.text }} 
          {...labelProps}
        >
          {label}
        </TextButtonLabel>
      ) : children}
    </Pressable>
  );
});

const styles = StyleSheet.create({
  base: {
    borderWidth: 1,
    alignItems: 'center', 
    justifyContent: 'center',
    flexDirection: 'row', // Ensure content aligns correctly
  },
});

BaseButton.displayName = 'BaseButton'; 