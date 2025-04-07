import React from 'react';
import { View, StyleSheet, Text, TextInput, TextInputProps, StyleProp, ViewStyle } from 'react-native';
import { BaseInput } from '../inputs/BaseInput'; // Import the single BaseInput
import { Theme, useTheme } from '../../theme';

interface AuthInputProps extends Omit<TextInputProps, 'style'> {
  label?: string;
  error?: boolean;
  errorMessage?: string;
  containerStyle?: StyleProp<ViewStyle>;
}

export const AuthInput = React.forwardRef<TextInput, AuthInputProps>((
  { label, error, errorMessage, containerStyle, ...props },
  ref
) => {
  const { theme } = useTheme();
  const styles = createStyles(theme);
  const errorTextStyle = {
    color: theme.colors.indicators.error,
    marginTop: theme.spacing.input.gap, // Use theme spacing
    fontSize: theme.typography.caption.fontSize,
    lineHeight: theme.typography.caption.lineHeight,
    fontFamily: theme.typography.caption.fontFamily,
  };

  return (
    <View style={[styles.outerContainer, containerStyle]}>
      <BaseInput
        ref={ref}
        error={error}
        placeholder={label} // TextInput uses placeholder
        // RNW handles translating placeholder to web attribute
        // For web accessibility, consider adding accessibilityLabel={label}
        accessibilityLabel={label} 
        {...props}
      />
      {error && errorMessage && (
        <Text style={[styles.errorTextBase, errorTextStyle]}>
          {errorMessage}
        </Text>
      )}
    </View>
  );
});

const createStyles = (theme: Theme) => StyleSheet.create({
  outerContainer: {
    width: '100%',
    marginBottom: theme.spacing.input.gap, // Use theme spacing
  },
  errorTextBase: {
    // Base styles for error text if needed, specific color/margin applied inline
  },
});

AuthInput.displayName = 'AuthInput'; 