import React from 'react';
import { View, ViewProps, StyleSheet, StyleProp, ViewStyle } from 'react-native';
import { useTheme } from '../../../theme';

interface BgViewProps extends ViewProps {
  children?: React.ReactNode;
  style?: StyleProp<ViewStyle>;
}

export const BgView = React.forwardRef<View, BgViewProps>((
  { children, style, ...props },
  ref
) => {
  const { theme } = useTheme();
  const viewStyle: ViewStyle = {
    backgroundColor: theme.colors.layout.background,
  };

  return (
    <View ref={ref} style={[viewStyle, style]} {...props}>
      {children}
    </View>
  );
});

BgView.displayName = 'BgView'; 