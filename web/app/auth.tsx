import React from 'react';
import { StyleSheet, View, Text } from 'react-native';
import { useTheme, Switch, BgView } from '@shared'; 
import { BrandSignature } from '../features/shared/BrandSignature'; // Corrected path

export default function AuthScreen() {
  console.log('AuthScreen');
  const { themePreference, setThemePreference, theme } = useTheme();

  const handleThemeToggle = (isDarkEnabled: boolean) => {
    setThemePreference(isDarkEnabled ? 'dark' : 'light');
  };

  const isSwitchOn = themePreference === 'dark';

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.layout.background }]}>
      <Text style={[styles.title, { color: theme.colors.text.primary }]}>Web Auth Page</Text>
      
      <View style={styles.switchContainer}>
        <Text style={{ color: theme.colors.text.secondary }}>Toggle Theme:</Text>
        <Switch 
          value={isSwitchOn}
          onValueChange={handleThemeToggle}
        />
      </View>

      {/* Using BgView might require specific web adjustments or remove if not needed */}
      <BgView style={styles.brandContainer}>
        <BrandSignature size={60} />
      </BgView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  switchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  brandContainer: {
    // Add styles if needed, separate from main container
  }
}); 