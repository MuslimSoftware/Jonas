import React from 'react';
import { Slot } from 'expo-router';
import { ThemeProvider } from '@shared/theme';
import { WebStorage } from '../src/lib/WebStorage'; // Correct path from app/_layout.tsx to src/lib

export default function RootLayout() {
  console.log('RootLayout');
  const storage = new WebStorage();

  return (
    <ThemeProvider storage={storage}>
      <Slot />
    </ThemeProvider>
  );
} 