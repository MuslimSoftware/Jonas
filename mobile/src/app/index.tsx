import React, { useEffect, useRef, useMemo } from 'react';
import { StyleSheet } from 'react-native';
import * as Updates from 'expo-updates';
import { useFonts } from 'expo-font';
import { useSplashAnimation } from '@/features/auth/hooks/useSplashAnimation';
import { AnimatedLogo } from '@/features/auth/components/AnimatedLogo';
import { BgView, MediumColumn } from '@/shared/components/layout';
import { PrimaryButton } from '@/shared/components/buttons';
import { TextBody } from '@/shared/components/text';

export default function SplashScreenComponent() {
  const [fontsLoaded, fontError] = useFonts({
    'Roboto-Regular': require('@/assets/fonts/Roboto-Regular.ttf'),
    'Roboto-Medium': require('@/assets/fonts/Roboto-Medium.ttf'),
    'Roboto-Bold': require('@/assets/fonts/Roboto-Bold.ttf'),
    'Roboto-Light': require('@/assets/fonts/Roboto-Light.ttf'),
  });

  const resolveRef = useRef<(() => void) | null>(null);
  const rejectRef = useRef<((reason?: any) => void) | null>(null);
  const promiseResolvedOrRejected = useRef(false);

  const fontsLoadedPromise = useMemo(
    () => new Promise<void>((resolve, reject) => {
      resolveRef.current = resolve;
      rejectRef.current = reject;
    }),
    []
  );

  useEffect(() => {
    if (promiseResolvedOrRejected.current) return;

    if (fontError) {
      console.error("[Font Loading Error]:", fontError);
      rejectRef.current?.(fontError);
      promiseResolvedOrRejected.current = true;
    } else if (fontsLoaded) {
      console.log("[Fonts Loaded Successfully]");
      resolveRef.current?.();
      promiseResolvedOrRejected.current = true;
    }
  }, [fontsLoaded, fontError]);

  const { animatedStyle } = useSplashAnimation(fontsLoadedPromise);

  if (fontError) {
    const handleRestartApp = async () => {
      try {
        await Updates.reloadAsync();
      } catch (e) {
        console.error("Error reloading app: ", e);
      }
    }

    return (
      <BgView style={styles.container}>
        <MediumColumn>
          <TextBody style={styles.errorText}>
            Something went wrong. Please try restarting the app. If the problem persists, please contact support.
          </TextBody>

          <PrimaryButton
            onPress={handleRestartApp}
            label="Restart App"
          />
        </MediumColumn>
      </BgView>
    );
  }

  return (
    <BgView style={styles.container}>
      <AnimatedLogo animatedStyle={animatedStyle} />
    </BgView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  errorText: {
    textAlign: 'center',
    padding: 20,
  },
});
