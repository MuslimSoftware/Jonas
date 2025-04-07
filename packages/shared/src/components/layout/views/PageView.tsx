import React from 'react';
import { View, StyleSheet, ViewProps, StyleProp, ViewStyle } from 'react-native';
import { Theme, useTheme } from '../../../theme';

interface PageViewProps extends ViewProps {
  children: React.ReactNode;
  style?: StyleProp<ViewStyle>;
}

export const PageView = React.forwardRef<View, PageViewProps>((
  { children, style, ...props },
  ref
) => {
  const { theme } = useTheme();
  const styles = createStyles(theme);
  return (
    <View ref={ref} style={[styles.container, style]} {...props}>
      {children}
    </View>
  );
});

const createStyles = (theme: Theme) => StyleSheet.create({
  container: {
    flex: 1,
    paddingHorizontal: theme.spacing.section.padding, 
  },
});

PageView.displayName = 'PageView'; 