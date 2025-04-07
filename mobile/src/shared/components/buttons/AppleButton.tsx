import React from 'react'
import {
  IconButton,
  IconButtonProps,
} from '@jonas/shared/src/components/buttons/IconButton'
import { AntDesign } from '@expo/vector-icons' // Import icons
import { iconSizes } from '@jonas/shared'

// Extend IconButtonProps, omitting things we'll set internally
type AppleButtonProps = Omit<
  IconButtonProps,
  'label' | 'icon' | 'variant' | 'style' | 'textColor'
>

export const AppleButton = (props: AppleButtonProps) => {
  // Define Apple-specific styles
  const appleStyle = {
    backgroundColor: '#000000', // Apple black
    borderWidth: 1,
    borderColor: '#dadce0', // Standard Google border color (light gray)
  }

  const appleTextColor = '#ffffff' // Apple white text

  return (
    <IconButton
      label="Continue with Apple"
      icon={
        <AntDesign
          name="apple1"
          size={iconSizes.medium}
          color={appleTextColor}
        />
      } // Use AntDesign icon
      variant="primary" // Use primary variant just as base, color overridden by style
      style={appleStyle}
      textColor={appleTextColor}
      {...props} // Pass down other props like onPress
    />
  )
}
