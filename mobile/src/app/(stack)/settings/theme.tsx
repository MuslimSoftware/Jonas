import React from 'react';
import { StyleSheet, useColorScheme, Switch } from 'react-native';
import { useTheme } from '@jonas/shared/src/theme';
import { FgView, LargeRow, MediumRow } from '@jonas/shared/src/components/layout';
import { TextBody } from '@jonas/shared/src/components/text';
import { paddings, borderRadii, lightTheme, darkTheme } from '@jonas/shared/src/theme';
import { SettingsPageLayout } from '@/features/settings/components/SettingsPageLayout';
import { ThemeCard } from '@/features/settings/components/ThemeCard';
import { ThemedSwitch as SharedThemedSwitch } from '@jonas/shared/src/components/forms/ThemedSwitch';

// Log the Switch imported directly in the mobile app
console.log('[Mobile App] Imported Switch:', Switch);

export default function ThemeSettingsScreen() {
  const { themePreference, setThemePreference } = useTheme();
  const systemColorScheme = useColorScheme();

  const handleSelectTheme = (selectedPreference: 'light' | 'dark') => {
    setThemePreference(selectedPreference);
  };

  const handleSystemToggle = (useSystem: boolean) => {
    if (useSystem) {
      setThemePreference('system');
    } else {
      setThemePreference(systemColorScheme ?? 'light');
    }
  };

  const isLightSelected = themePreference === 'light';
  const isDarkSelected = themePreference === 'dark';
  const useSystemSelected = themePreference === 'system';

  return (
    <SettingsPageLayout title="Theme">
      <FgView style={styles.sectionContent}>
        <MediumRow style={styles.toggleRow}>
          <TextBody>Use System Setting</TextBody>
          {/* Use the imported SharedThemedSwitch to trigger its log */}
          <SharedThemedSwitch 
            onValueChange={handleSystemToggle}
            value={useSystemSelected}
          /> 
        </MediumRow>
      </FgView>
      {/* Explicit Theme Choices - Only show if system is OFF */}
      {!useSystemSelected && (
        <LargeRow style={styles.cardContainer}>
          <ThemeCard 
            theme={lightTheme}
            isThemeDark={false}
            isSelected={isLightSelected}
            onPress={() => handleSelectTheme('light')}
          />
          <ThemeCard 
            theme={darkTheme}
            isThemeDark={true}
            isSelected={isDarkSelected}
            onPress={() => handleSelectTheme('dark')}
          />
        </LargeRow>
      )}
    </SettingsPageLayout>
  );
}

const styles = StyleSheet.create({
  cardContainer: {
    paddingHorizontal: paddings.small,
  },
  sectionContent: {
    borderRadius: borderRadii.large,
    overflow: 'hidden',
    padding: paddings.large,
  },
  toggleRow: {
    justifyContent: 'space-between',
  },
}); 