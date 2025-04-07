import React from 'react';
import { IconButton, IconButtonProps } from './IconButton';
import { TouchableOpacity } from 'react-native';

// SecondaryButton implicitly requires theme because IconButton does
export type SecondaryButtonProps = Omit<IconButtonProps, 'variant'>;

export const SecondaryButton = React.forwardRef<
  React.ElementRef<typeof TouchableOpacity>,
  SecondaryButtonProps
>(({ ...props }, ref) => {
  // Pass all props down, setting variant to 'secondary'
  return <IconButton ref={ref} variant="secondary" {...props} />;
});

SecondaryButton.displayName = 'SecondaryButton'; 