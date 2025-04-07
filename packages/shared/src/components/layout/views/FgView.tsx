import React from 'react';
import { View, ViewProps, StyleSheet, StyleProp, ViewStyle } from 'react-native';
import { useTheme } from '../../../theme';

interface FgViewProps extends ViewProps {
  children?: React.ReactNode;
  style?: StyleProp<ViewStyle>;
}

export const FgView = React.forwardRef<View, FgViewProps>((
  { children, style, ...props },
  ref
) => {
  const { theme } = useTheme();
  const viewStyle: ViewStyle = {
    backgroundColor: theme.colors.layout.foreground,
  };

  return (
    <View ref={ref} style={[viewStyle, style]} {...props}>
      {children}
    </View>
  );
});

FgView.displayName = 'FgView'; 