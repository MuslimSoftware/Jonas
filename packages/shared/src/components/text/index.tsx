import React from 'react';
import { ThemedText, TextAliasProps } from './ThemedText';

export * from './ThemedText';
export * from './TextLink';

// Note: Theme is now handled internally by ThemedText via useTheme

export function TextHeader(props: TextAliasProps) {
  return <ThemedText accessibilityRole="header" accessibilityLevel={1} variant="h1" {...props} />;
}

export function TextHeaderTwo(props: TextAliasProps) {
  return <ThemedText accessibilityRole="header" accessibilityLevel={2} variant="h2" {...props} />;
}

export function TextHeaderThree(props: TextAliasProps) {
  return <ThemedText accessibilityRole="header" accessibilityLevel={3} variant="h3" {...props} />;
}

export function TextHeaderFour(props: TextAliasProps) {
  return <ThemedText accessibilityRole="header" accessibilityLevel={4} variant="h4" {...props} />;
}

export function TextBody(props: TextAliasProps) {
  return <ThemedText variant="body1" {...props} />;
}

export function TextSubtitle(props: TextAliasProps) {
  return <ThemedText variant="body2" {...props} />;
}

export function TextCaption(props: TextAliasProps) {
  return <ThemedText variant="caption" {...props} />;
}

export function TextButtonLabel(props: TextAliasProps) {
  return <ThemedText variant="button" {...props} />;
} 