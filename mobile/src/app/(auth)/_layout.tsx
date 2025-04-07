import { Stack } from 'expo-router'

export default function AuthLayout() {
  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="landing" options={{ title: 'Welcome' }} />
      <Stack.Screen name="email" options={{ title: 'Enter Email' }} />
      <Stack.Screen name="otp" options={{ title: 'Verify OTP' }} />
    </Stack>
  )
}
