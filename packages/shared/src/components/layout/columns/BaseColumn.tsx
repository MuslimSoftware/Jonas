import React from 'react';
import { View, StyleSheet, StyleProp, ViewStyle, ViewProps } from 'react-native';

// Define props inline for clarity
export interface BaseColumnProps extends ViewProps {
  gap?: number;
  children?: React.ReactNode;
  style?: StyleProp<ViewStyle>;
}

export const BaseColumn = React.forwardRef<View, BaseColumnProps>((
  { children, gap, style, ...props }, // Destructure props correctly
  ref
) => {
  // Combine base styles, gap, and passed styles
  const combinedStyle = StyleSheet.flatten([
    styles.base, 
    { gap: gap ?? 0 },
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
    flexDirection: 'column', 
  },
});

BaseColumn.displayName = 'BaseColumn'; 