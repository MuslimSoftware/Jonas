import {
  StyleSheet,
  ScrollView,
  Platform,
  Pressable,
  Image,
  View,
} from 'react-native'
import { useTheme } from '@jonas/shared/src/theme'
import { useSafeAreaInsets } from 'react-native-safe-area-context'
import { useRouter } from 'expo-router'
import {
  TextBody,
  TextHeader,
  TextCaption,
  TextHeaderTwo,
} from '@jonas/shared/src/components/text'
import { Ionicons } from '@expo/vector-icons'
import {
  MediumColumn,
  BaseColumn,
  BgView,
  FgView,
  SmallColumn,
} from '@jonas/shared/src/components/layout'
import { paddings, gaps, borderRadii, iconSizes } from '@jonas/shared'

export default function ProfileScreen() {
  const { theme, isDark } = useTheme()
  const insets = useSafeAreaInsets()
  const router = useRouter()

  const handleSettingsPress = () => {
    router.push('/settings')
  }

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
        <BaseColumn style={styles.content} gap={gaps.large}>
          <View style={styles.header}>
            <TextHeader>Profile</TextHeader>
            <Pressable
              onPress={handleSettingsPress}
              style={({ pressed }) => [
                styles.settingsButton,
                { opacity: pressed ? 0.7 : 1 },
              ]}
              hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
            >
              <Ionicons
                name="settings-outline"
                size={iconSizes.medium}
                color={theme.colors.text.primary}
              />
            </Pressable>
          </View>

          <FgView style={styles.profileCard}>
            <BaseColumn gap={gaps.medium}>
              <View style={styles.profileInfo}>
                <View
                  style={[
                    styles.avatarPlaceholder,
                    { backgroundColor: theme.colors.layout.border },
                  ]}
                >
                  <Image
                    source={require('@/assets/images/icon.png')}
                    style={styles.avatar}
                  />
                </View>
                <SmallColumn style={styles.nameContainer}>
                  <TextHeaderTwo>Younes Benketira</TextHeaderTwo>
                  <TextCaption
                    style={styles.username}
                    color={theme.colors.text.secondary}
                  >
                    @younesbenketira
                  </TextCaption>
                </SmallColumn>
              </View>
              <View style={styles.locationContainer}>
                <Ionicons
                  name="location-outline"
                  size={iconSizes.small}
                  color={theme.colors.text.secondary}
                />
                <TextCaption
                  style={styles.locationText}
                  color={theme.colors.text.secondary}
                >
                  Montreal, QC
                </TextCaption>
              </View>
            </BaseColumn>
          </FgView>

          <FgView style={styles.section}>
            <MediumColumn>
              <View style={styles.sectionHeader}>
                <TextBody>About</TextBody>
              </View>
              <TextBody color={theme.colors.text.secondary}>
                Software developer passionate about creating amazing user
                experiences. Love building beautiful and functional apps.
              </TextBody>
            </MediumColumn>
          </FgView>

          <FgView style={styles.section}>
            <MediumColumn>
              <View style={styles.sectionHeader}>
                <TextBody>Contact</TextBody>
              </View>
              <BaseColumn gap={gaps.small}>
                <View style={styles.contactItem}>
                  <Ionicons
                    name="mail-outline"
                    size={iconSizes.xsmall}
                    color={theme.colors.text.secondary}
                  />
                  <TextCaption
                    style={styles.contactText}
                    color={theme.colors.text.secondary}
                  >
                    me@younesbenketira.com
                  </TextCaption>
                </View>
                <View style={styles.contactItem}>
                  <Ionicons
                    name="link-outline"
                    size={iconSizes.xsmall}
                    color={theme.colors.text.secondary}
                  />
                  <TextCaption
                    style={styles.contactText}
                    color={theme.colors.text.secondary}
                  >
                    github.com/younesbenketira
                  </TextCaption>
                </View>
              </BaseColumn>
            </MediumColumn>
          </FgView>
        </BaseColumn>
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
    paddingHorizontal: paddings.medium,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  settingsButton: {
    padding: paddings.xsmall,
    alignItems: 'center',
    justifyContent: 'center',
  },
  editButton: {
    padding: paddings.small,
  },
  profileCard: {
    padding: paddings.large,
    borderRadius: borderRadii.large,
  },
  profileInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: gaps.medium,
  },
  avatarPlaceholder: {
    width: 65,
    height: 65,
    borderRadius: 32.5,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatar: {
    width: 60,
    height: 60,
    borderRadius: 30,
  },
  nameContainer: {
    flex: 1,
  },
  username: {
    opacity: 0.7,
  },
  locationContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: gaps.xsmall,
  },
  locationText: {
    flex: 1,
  },
  section: {
    padding: paddings.large,
    borderRadius: borderRadii.large,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  contactItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: gaps.small,
  },
  contactText: {
    flex: 1,
  },
})
