import React from 'react';
import { TextInput, View, StyleSheet, TextInputProps, ViewStyle, StyleProp, TextStyle, Platform } from 'react-native';
import { Theme } from '../../theme';
import { useTheme } from '../../theme/ThemeContext';

interface BaseInputProps extends Omit<TextInputProps, 'style'> {
  inputStyle?: StyleProp<TextStyle>;
  containerStyle?: StyleProp<ViewStyle>;
  error?: boolean;
  onFocus?: (e: any) => void;
  onBlur?: (e: any) => void;
}

export const BaseInput = React.forwardRef<TextInput, BaseInputProps>((
  { inputStyle, containerStyle, error, onFocus, onBlur, ...props },
  ref
) => {
  const { theme } = useTheme();
  const [isFocused, setIsFocused] = React.useState(false);
  const styles = createStyles(theme, error, isFocused);

  const handleFocus = (e: any) => {
    setIsFocused(true);
    onFocus?.(e);
  };

  const handleBlur = (e: any) => {
    setIsFocused(false);
    onBlur?.(e);
  };

  return (
    <View style={[styles.container, containerStyle]}>
      <TextInput
        ref={ref}
        style={[styles.input, inputStyle]}
        placeholderTextColor={theme.colors.text.secondary}
        onFocus={handleFocus}
        onBlur={handleBlur}
        {...props}
      />
    </View>
  );
});

const createStyles = (theme: Theme, error?: boolean, isFocused?: boolean) => StyleSheet.create({
  container: {
    width: '100%',
  },
  input: {
    width: '100%',
    borderWidth: 1,
    borderRadius: theme.spacing.input.borderRadius,
    padding: theme.spacing.input.padding,
    fontSize: theme.typography.body1.fontSize,
    fontFamily: theme.typography.body1.fontFamily,
    backgroundColor: theme.colors.layout.background,
    color: theme.colors.text.primary,
    borderColor: error 
      ? theme.colors.indicators.error 
      : isFocused
      ? theme.colors.brand.primary 
      : theme.colors.layout.border,
    ...Platform.select({
      web: {
        outlineWidth: isFocused ? 2 : 0, 
        outlineStyle: 'solid',
        outlineColor: error ? theme.colors.indicators.error : theme.colors.brand.primary,
        transition: 'border-color 0.2s ease, outline-color 0.2s ease',
      },
      default: { }
    })
  } as any,
});

BaseInput.displayName = 'BaseInput'; 