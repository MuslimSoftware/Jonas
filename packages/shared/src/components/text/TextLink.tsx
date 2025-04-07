import React from 'react';
import { Text, TextStyle } from 'react-native';
// Import ThemedTextProps which no longer requires theme
import { ThemedText, ThemedTextProps } from './ThemedText'; 

// Remove theme from TextLink props as ThemedText gets it from context
export const TextLink = React.forwardRef<Text, ThemedTextProps>((
  { variant = 'caption', style, ...props },
  ref
) => {
  const underlineStyle: TextStyle = {
    textDecorationLine: 'underline',
  };

  return (
    <ThemedText
      ref={ref as React.Ref<Text>} // Keep cast for now
      accessibilityRole="link" 
      variant={variant}
      style={[underlineStyle, style]} 
      {...props} // theme is handled internally by ThemedText now
    />
  );
});

TextLink.displayName = 'TextLink'; 