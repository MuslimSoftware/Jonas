import React from 'react'
import {
  TextInput,
  View,
  StyleSheet,
  TextInputProps,
  ViewStyle,
  StyleProp,
  TextStyle,
} from 'react-native'
import { useTheme } from '@/shared/context/ThemeContext'
import { paddings, borderRadii } from '@uniskit/shared'

interface BaseInputProps extends Omit<TextInputProps, 'style'> {
  inputStyle?: StyleProp<TextStyle>
  containerStyle?: ViewStyle
  error?: boolean
  label?: string
}

export const BaseInput: React.FC<BaseInputProps> = ({
  inputStyle,
  containerStyle,
  error,
  label,
  ...props
}) => {
  const { theme } = useTheme()

  const computedInputStyles = [
    styles.input,
    {
      backgroundColor: theme.colors.layout.background,
      color: theme.colors.text.primary,
      borderColor: error
        ? theme.colors.indicators.error
        : theme.colors.layout.border,
    },
    inputStyle,
  ]

  return (
    <View style={[styles.container, containerStyle]}>
      <TextInput
        style={computedInputStyles}
        placeholderTextColor={theme.colors.text.secondary}
        {...props}
      />
    </View>
  )
}

const styles = StyleSheet.create({
  container: {
    width: '100%',
  },
  input: {
    width: '100%',
    borderWidth: 1,
    borderRadius: borderRadii.medium,
    padding: paddings.medium,
    fontSize: 16, // Consider adding this to theme.typography
    // Add other base styles as needed
  },
})
