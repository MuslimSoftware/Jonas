import React from 'react';
import { IconButton, IconButtonProps } from './IconButton';
import { TouchableOpacity } from 'react-native'; // Import TouchableOpacity for ref type

// PrimaryButton implicitly requires theme because IconButton does
export type PrimaryButtonProps = Omit<IconButtonProps, 'variant'>;

export const PrimaryButton = React.forwardRef<
  React.ElementRef<typeof TouchableOpacity>, 
  PrimaryButtonProps
>(({ ...props }, ref) => {
  return <IconButton ref={ref} variant="primary" {...props} />;
});

PrimaryButton.displayName = 'PrimaryButton'; 