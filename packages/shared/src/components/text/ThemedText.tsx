import React from 'react';
import { Text, TextProps, TextStyle, StyleProp, Platform, AccessibilityRole, StyleSheet } from 'react-native';
import { Typography, Theme, useTheme } from '../../theme'; // Corrected relative path

export type TextVariant = keyof Typography;

export interface ThemedTextProps extends Omit<TextProps, 'style' | 'accessibilityRole'> { // Omit style and accessibilityRole from base RN props
  children: React.ReactNode;
  variant?: TextVariant;
  style?: StyleProp<TextStyle>; // Accept custom style prop
  color?: string;
  accessibilityRole?: AccessibilityRole | 'paragraph' | 'link' | string; // Allow specific roles + RN type
  accessibilityLevel?: number; // For headings on web (h1-h6)
  href?: string; // For links on web
  target?: string; // For links on web
}

// This helper might need adjustment based on font loading in web/mobile
// Or might not be needed if RNW handles font weights well
const getFontFamilyForWeight = (theme: Theme, variant: TextVariant): string | undefined => {
  // Simpler approach: rely on default font family in theme/RNW
  return theme.typography[variant]?.fontFamily; // Return font family from theme if defined
};

export const ThemedText = React.forwardRef<Text, ThemedTextProps>((
  { children, variant = 'body1', style, color, 
    accessibilityRole = 'paragraph', 
    accessibilityLevel, 
    href, 
    target, 
    ...props },
  ref
) => {
  const { theme } = useTheme(); // Use the hook here
  const variantStyle = theme.typography[variant] || theme.typography.body1;

  const baseTextStyle: TextStyle = {
    fontSize: variantStyle.fontSize,
    fontWeight: variantStyle.fontWeight.toString() as any, 
    lineHeight: variantStyle.lineHeight,
    color: color || theme.colors.text.primary,
  };

  // Define web-specific style props that ARE valid TextStyle props
  const webOnlyStyles: TextStyle = Platform.select({
    web: {
      cursor: href ? 'pointer' : undefined, // RNW supports cursor
      // wordWrap removed - handle via parent container styles if needed
    },
    default: {}
  });

  // Use StyleSheet.flatten directly
  const finalStyle = StyleSheet.flatten([baseTextStyle, webOnlyStyles, style]);

  // Prepare web link attributes
  const webLinkProps = Platform.OS === 'web' && href ? {
    href: href,
    target: target,
    rel: target === '_blank' ? 'noopener noreferrer' : undefined,
  } : {};

  return (
    <Text 
      ref={ref}
      style={finalStyle}
      accessibilityRole={accessibilityRole as AccessibilityRole}
      aria-level={accessibilityLevel} 
      {...webLinkProps} 
      {...props} 
    >
      {children}
    </Text>
  );
});

ThemedText.displayName = 'ThemedText';

// Type for aliases remains the same
export type TextAliasProps = Omit<ThemedTextProps, 'variant' | 'theme'>; 