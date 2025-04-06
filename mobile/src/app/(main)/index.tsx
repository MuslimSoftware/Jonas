import { StyleSheet, Platform, View, ScrollView } from 'react-native'
import { useTheme } from '@/shared/context/ThemeContext'
import { useSafeAreaInsets } from 'react-native-safe-area-context'
import { TextBody, TextHeader } from '@/shared/components/text'
import { Ionicons } from '@expo/vector-icons'
import { LargeColumn, BgView, SmallColumn } from '@/shared/components/layout'
import { paddings, gaps, borderRadii } from '@uniskit/shared'

export default function HomeScreen() {
  const { theme } = useTheme()
  const insets = useSafeAreaInsets()

  const TAB_BAR_HEIGHT = 60
  const defaultPadding = paddings.medium

  return (
    <BgView style={styles.container}>
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={[
          styles.scrollContent,
          {
            paddingTop: insets.top + defaultPadding,
            paddingBottom:
              Platform.OS === 'ios'
                ? insets.bottom + TAB_BAR_HEIGHT
                : insets.bottom + defaultPadding,
          },
        ]}
      >
        <LargeColumn style={styles.content}>
          <View style={styles.iconContainer}>
            <Ionicons
              name="home"
              size={64}
              color={theme.colors.brand.primary}
              style={{ opacity: 0.8 }}
            />
          </View>

          <View style={styles.section}>
            <TextHeader style={styles.title}>Thank You!</TextHeader>
            <TextBody
              style={[
                styles.description,
                { color: theme.colors.text.secondary },
              ]}
            >
              Thanks for using my React Native template. This template includes:
            </TextBody>
            <SmallColumn style={styles.features}>
              <TextBody style={{ color: theme.colors.text.secondary }}>
                • Beautiful dark/light theme
              </TextBody>
              <TextBody style={{ color: theme.colors.text.secondary }}>
                • Type-safe navigation
              </TextBody>
              <TextBody style={{ color: theme.colors.text.secondary }}>
                • Authentication flow
              </TextBody>
              <TextBody style={{ color: theme.colors.text.secondary }}>
                • Consistent styling system
              </TextBody>
              <TextBody style={{ color: theme.colors.text.secondary }}>
                • iOS & Android support
              </TextBody>
            </SmallColumn>
          </View>

          <View style={[styles.section]}>
            <TextBody style={styles.tip}>
              💡 Start by modifying the files in the{' '}
              <TextBody style={{ color: theme.colors.brand.primary }}>
                app/
              </TextBody>{' '}
              directory to build your app!
            </TextBody>
          </View>
        </LargeColumn>
      </ScrollView>
    </BgView>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
  },
  content: {
    flex: 1,
    paddingHorizontal: paddings.large,
  },
  iconContainer: {
    alignItems: 'center',
    marginTop: paddings.xlarge,
  },
  section: {
    padding: paddings.large,
    borderRadius: borderRadii.large,
  },
  title: {
    textAlign: 'center',
    marginBottom: gaps.small,
  },
  description: {
    textAlign: 'center',
    marginBottom: gaps.medium,
  },
  features: {
    alignItems: 'flex-start',
    marginLeft: paddings.large,
  },
  tip: {
    textAlign: 'center',
    lineHeight: 24,
    paddingHorizontal: paddings.small,
  },
})
