import { View, ViewStyle } from 'react-native'
import { useTheme } from '@/shared/context/ThemeContext'

export const BgView = ({
  children,
  style,
}: {
  children?: React.ReactNode
  style?: ViewStyle
}) => {
  const { theme } = useTheme()

  return (
    <View style={[{ backgroundColor: theme.colors.layout.background }, style]}>
      {children}
    </View>
  )
}
