import {
  TouchableOpacity,
  TouchableOpacityProps,
  StyleSheet,
  StyleProp,
  ViewStyle,
  ColorValue,
} from 'react-native'
import { useTheme } from '@/shared/context/ThemeContext'
import { paddings, borderRadii, gaps } from '@uniskit/shared'
import React from 'react'
import { MediumRow } from '@/shared/components/layout'
import { TextButtonLabel } from '../text'

export interface BaseButtonProps
  extends Omit<TouchableOpacityProps, 'children'> {
  children: React.ReactNode
  variant?: 'primary' | 'secondary'
  disabled?: boolean
}

export const BaseButton = ({
  children,
  variant = 'primary',
  disabled = false,
  style,
  ...props
}: BaseButtonProps) => {
  const { theme } = useTheme()

  // Determine the effective variant based on the disabled state
  const effectiveVariant = disabled ? 'disabled' : variant

  // Get colors from the theme using the effective variant
  const buttonThemeStyles = theme.colors.button[effectiveVariant]

  const buttonStyle: StyleProp<ViewStyle> = [
    {
      // Use colors from the determined variant (primary, secondary, or disabled)
      backgroundColor: buttonThemeStyles.background as ColorValue,
      borderColor: buttonThemeStyles.border as ColorValue,
      borderWidth: 1, // Ensure border is visible
      padding: paddings.base,
      borderRadius: borderRadii.xxlarge,
    },
    style,
  ]

  return (
    <TouchableOpacity
      style={buttonStyle}
      disabled={disabled}
      activeOpacity={0.8}
      {...props}
    >
      <MediumRow style={styles.contentContainer}>
        {children}
      </MediumRow>
    </TouchableOpacity>
  )
}

const styles = StyleSheet.create({
  contentContainer: {
    justifyContent: 'center',
    alignItems: 'center',
  },
})
