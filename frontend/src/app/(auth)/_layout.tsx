import { Stack } from 'expo-router'
import React, { useEffect } from 'react'
import { useRouter } from 'expo-router'
import { useAuth } from '@/features/auth/context/AuthContext'

export default function AuthLayout() {
  const { isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated) {
      router.replace('/chat');
    }
  }, [isAuthenticated]);

  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="landing" options={{ title: 'Welcome' }} />
      <Stack.Screen name="email" options={{ title: 'Enter Email' }} />
      <Stack.Screen name="otp" options={{ title: 'Verify OTP' }} />
    </Stack>
  )
}
