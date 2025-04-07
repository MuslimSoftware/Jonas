import { Stack } from 'expo-router'
import { useTheme } from '@jonas/shared/src/theme'

export default function StackLayout() {
  const { theme } = useTheme()

  return (
    <Stack
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: theme.colors.layout.background },
      }}
    >
      <Stack.Screen name="settings/theme" />
    </Stack>
  )
}
