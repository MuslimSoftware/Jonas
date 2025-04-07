import React from 'react'
import { useFonts } from 'expo-font'
import { Stack } from 'expo-router'
import * as SplashScreen from 'expo-splash-screen'
import { StatusBar } from 'expo-status-bar'
import { useEffect } from 'react'
import 'react-native-reanimated'
import { ThemeProvider, useTheme } from '@jonas/shared/src/theme/ThemeContext'
import { AuthProvider } from '@/features/auth/context/AuthContext'
import { MobileStorage } from '../lib/MobileStorage'

// Keep the splash screen visible while we fetch resources
SplashScreen.preventAutoHideAsync()

const mobileStorage = new MobileStorage()

function RootLayoutNav() {
  const { isDark, theme } = useTheme()

  return (
    <>
      <Stack
        screenOptions={{
          headerShown: false,
          animation: 'slide_from_right',
        }}
      >
        <Stack.Screen
          name="index"
          options={{
            animation: 'none',
          }}
        />
        <Stack.Screen
          name="(auth)"
          options={{
            animation: 'none',
          }}
        />
        <Stack.Screen
          name="(main)"
          options={{
            animation: 'none',
          }}
        />
        <Stack.Screen name="+not-found" />
      </Stack>
      <StatusBar
        style={isDark ? 'light' : 'dark'}
        backgroundColor={theme.colors.layout.background}
      />
    </>
  )
}

export default function RootLayout() {
  const [loaded] = useFonts({
    SpaceMono: require('@/assets/fonts/SpaceMono-Regular.ttf'),
  })

  useEffect(() => {
    if (loaded) {
      // Hide the splash screen after the fonts have loaded and the
      // UI is ready.
      SplashScreen.hideAsync()
    }
  }, [loaded])

  if (!loaded) {
    return null
  }

  return (
    <ThemeProvider storage={mobileStorage}>
      <AuthProvider>
        <RootLayoutNav />
      </AuthProvider>
    </ThemeProvider>
  )
}
