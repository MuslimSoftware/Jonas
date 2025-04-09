import { Tabs, Stack } from 'expo-router'
import React from 'react'
import { Platform, StyleSheet } from 'react-native'
import { useTheme } from '@/features/shared/context/ThemeContext'
import { Ionicons } from '@expo/vector-icons'

export default function TabLayout() {
  const { theme } = useTheme()

  if (Platform.OS === 'web') {
    return (
      <Stack
        screenOptions={{
          headerShown: false,
          contentStyle: { backgroundColor: theme.colors.layout.foreground }
        }}
      />
    )
  }

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: theme.colors.brand.primary,
        headerShown: false,
        tabBarStyle: {
          backgroundColor: theme.colors.layout.background,
          borderTopColor: theme.colors.layout.border,
          ...(Platform.OS === 'android' && {
            height: 60,
          }),
        },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'Home',
          tabBarIcon: ({ color, size, focused }) => (
            <Ionicons
              name={focused ? 'home' : 'home-outline'}
              size={size}
              color={color}
            />
          ),
          tabBarIconStyle: styles.tabBarIcon,
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Profile',
          tabBarIcon: ({ color, size, focused }) => (
            <Ionicons
              name={focused ? 'person' : 'person-outline'}
              size={size}
              color={color}
            />
          ),
          tabBarIconStyle: styles.tabBarIcon,
        }}
      />
      {/* Add Chat Tab for mobile if desired, or leave it out */}
      {/* Example:
      <Tabs.Screen
        name="chat" // Assuming you want a chat tab on mobile
        options={{
          title: 'Chat',
          tabBarIcon: ({ color, size, focused }) => (
            <Ionicons
              name={focused ? 'chatbubbles' : 'chatbubbles-outline'}
              size={size}
              color={color}
            />
          ),
          tabBarIconStyle: styles.tabBarIcon,
        }}
      />
      */}
    </Tabs>
  )
}

const styles = StyleSheet.create({
  tabBarIcon: {
    marginTop: 5,
  },
})
