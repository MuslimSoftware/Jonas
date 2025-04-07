import React from 'react';
import { View, StyleSheet, ViewProps, StyleProp, ViewStyle } from 'react-native';

// Assuming a shared type or define inline
export interface BaseLayoutComponentProps extends ViewProps {
  gap?: number;
  children?: React.ReactNode;
  style?: StyleProp<ViewStyle>;
}

export const BaseRow = React.forwardRef<View, BaseLayoutComponentProps>((
  { style, gap, children, ...props }, 
  ref
) => {
  // Combine base styles, gap, and passed styles
  const combinedStyle = StyleSheet.flatten([
    styles.base,
    { gap: gap ?? 0 }, // Apply gap if provided
    style, 
  ]);

  return (
    <View ref={ref} style={combinedStyle} {...props}>
      {children}
    </View>
  );
});

const styles = StyleSheet.create({
  base: {
    flexDirection: 'row', 
    alignItems: 'center', 
  },
});

BaseRow.displayName = 'BaseRow'; 