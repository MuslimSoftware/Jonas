import React from 'react'
import { Image, ImageStyle } from 'react-native'
import {
  IconButton,
  IconButtonProps,
} from '@jonas/shared/src/components/buttons/IconButton'
import { iconSizes } from '@jonas/shared'

// Extend IconButtonProps, omitting things we'll set internally
type GoogleButtonProps = Omit<
  IconButtonProps,
  'label' | 'icon' | 'variant' | 'style' | 'textColor'
>

export const GoogleButton = (props: GoogleButtonProps) => {
  // Define Google-specific styles with hardcoded colors
  const googleStyle = {
    backgroundColor: '#ffffff', // Always white
    borderWidth: 1,
    borderColor: '#dadce0', // Standard Google border color (light gray)
  }

  const googleTextColor = '#3c4043'

  const logoStyle: ImageStyle = {
    width: iconSizes.medium,
    height: iconSizes.medium,
  }

  return (
    <IconButton
      label="Continue with Google"
      icon={
        <Image
          source={require('@/assets/images/google_logo.png')}
          style={logoStyle}
        />
      }
      variant="secondary"
      style={googleStyle}
      textColor={googleTextColor}
      {...props}
    />
  )
}
