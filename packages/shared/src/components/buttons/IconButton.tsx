import React from 'react';
import { StyleProp, TextStyle, ViewStyle, TouchableOpacity } from 'react-native';
import { BaseButton, BaseButtonProps } from './BaseButton';
import { ThemedText, TextVariant, TextAliasProps } from '../text'; 
import { Theme, useTheme } from '../../theme';

// Extend BaseButtonProps, removing props handled by BaseButton directly
// Omit children, label, variant, disabled, theme, labelProps from BaseButtonProps
export interface IconButtonProps extends Omit<BaseButtonProps, 'children' | 'label' | 'variant' | 'disabled' | 'theme' | 'labelProps'> {
  label: string; // Label is mandatory here
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  textVariant?: TextVariant; // Specific text variant for this button
  // Explicit textColor is better handled by passing theme/variant
  // textColor?: string; 
  textStyle?: StyleProp<TextStyle>; // Additional custom text styles
  variant?: BaseButtonProps['variant']; // Re-add variant if needed
  disabled?: boolean;
  textColor?: string; // *** Add optional textColor prop ***
}

export const IconButton = React.forwardRef<React.ElementRef<typeof TouchableOpacity>, IconButtonProps>((
  { 
    label, 
    icon, 
    iconPosition = 'left', 
    variant = 'primary', // Default variant
    textVariant = 'button', 
    textStyle,
    style,
    disabled = false,
    textColor, // *** Destructure textColor ***
    ...props 
  },
  ref
) => {
  const { theme } = useTheme();
  const effectiveVariant = disabled ? 'disabled' : variant;
  const buttonThemeStyles = theme.colors.button[effectiveVariant];

  // Determine the final text color: use textColor prop if provided, otherwise use theme
  const finalTextColor = textColor || buttonThemeStyles.text;

  // Pass theme to ThemedText
  const textElement = (
    <ThemedText
      variant={textVariant}
      style={[{ color: finalTextColor }, textStyle]}
    >
      {label}
    </ThemedText>
  );

  // Construct content based on icon position
  const content = React.Children.toArray([
      iconPosition === 'left' && icon,
      textElement,
      iconPosition === 'right' && icon,
    ]).filter(Boolean);

  return (
    <BaseButton 
      ref={ref}
      variant={variant} 
      style={style} 
      disabled={disabled} 
      {...props}
    >
      {content}
    </BaseButton>
  );
});

IconButton.displayName = 'IconButton'; 