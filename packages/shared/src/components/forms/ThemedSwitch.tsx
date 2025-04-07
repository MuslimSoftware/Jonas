import React from 'react';
import { Switch , SwitchProps as RNSwitchProps, Platform } from 'react-native';
import { Theme, useTheme } from '../../theme';

export interface ThemedSwitchProps extends RNSwitchProps {}

export const ThemedSwitch = (props: ThemedSwitchProps) => {
  const { theme } = useTheme();
  const trackColor = {
    false: theme.colors.layout.foreground, 
    true: theme.colors.brand.primary
  };

  return <Switch
    trackColor={trackColor}
    {...props} // Pass all received props down
  />
}