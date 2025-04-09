import { Tabs, Stack } from 'expo-router'
import React from 'react'
import { Platform, StyleSheet } from 'react-native'
import { useTheme } from '@/features/shared/context/ThemeContext'
import { Ionicons } from '@expo/vector-icons'

export default function TabLayout() {
  const { theme } = useTheme()

  return (
    <Stack
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: theme.colors.layout.foreground }
      }}
    >
      <Stack.Screen name="chat" />
    </Stack>
  )
}
