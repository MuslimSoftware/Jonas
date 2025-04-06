import { useEffect, useRef, useCallback } from 'react'
import { Animated } from 'react-native'
import { router } from 'expo-router'
import * as SecureStore from 'expo-secure-store'
import * as SplashScreen from 'expo-splash-screen'

export function useSplashAnimation(onFontsLoaded: Promise<void>) {
  // Refs for animated values
  const scaleAnim = useRef(new Animated.Value(0.3)).current
  const opacityAnim = useRef(new Animated.Value(0)).current
  const breatheAnim = useRef(new Animated.Value(1)).current

  // Refs for controlling flow and state
  const isMountedRef = useRef(true)
  const isLoadingCompleteRef = useRef(false)
  const isAuthenticatedRef = useRef(false)
  const currentAnimationRef = useRef<Animated.CompositeAnimation | null>(null)

  // Initial fade-in and scale-up animation
  const initialAnimationRef = useRef(
    Animated.parallel([
      Animated.spring(scaleAnim, {
        toValue: 1,
        tension: 20,
        friction: 2,
        useNativeDriver: true,
      }),
      Animated.timing(opacityAnim, {
        toValue: 1,
        duration: 500,
        useNativeDriver: true,
      }),
    ])
  ).current

  // Single breathing cycle animation (inhale/exhale)
  const createBreathingAnimation = useCallback(() => {
    return Animated.sequence([
      Animated.timing(breatheAnim, {
        toValue: 1.1,
        duration: 1000,
        useNativeDriver: true,
      }),
      Animated.timing(breatheAnim, {
        toValue: 1,
        duration: 1000,
        useNativeDriver: true,
      }),
    ])
  }, [breatheAnim])
  
  // Triggers navigation and hides splash screen
  const triggerFinalNavigation = useCallback(() => {
    if (!isMountedRef.current) return
    try {
      const targetRoute = isAuthenticatedRef.current ? '/(main)' : '/(auth)/landing'
      router.replace(targetRoute)
    } catch (error) {
      router.replace('/(auth)/landing') // Fallback
    } finally {
      SplashScreen.hideAsync()
    }
  }, [])

  // Runs a single breathing cycle and decides whether to loop or finish
  const runBreathingCycle = useCallback(() => {
    if (!isMountedRef.current) {
      return
    }
    currentAnimationRef.current = createBreathingAnimation()
    currentAnimationRef.current.start(({ finished }) => {
      if (!finished || !isMountedRef.current) {
        return
      }
      
      if (isLoadingCompleteRef.current) {
        triggerFinalNavigation()
      } else {
        runBreathingCycle()
      }
    })
  }, [createBreathingAnimation, triggerFinalNavigation])

  // Checks authentication status using SecureStore
  const checkAuthStatus = useCallback(async (): Promise<boolean> => {
    try {
      const refreshToken = await SecureStore.getItemAsync('refresh_token')
      const isAuthenticated = !!refreshToken
      isAuthenticatedRef.current = isAuthenticated
      return isAuthenticated
    } catch (error) {
      console.error("[SplashAnimation] SecureStore error checking auth:", error)
      isAuthenticatedRef.current = false // Default to false on error
      return false
    }
  }, [])

  // Main effect coordinating the animation and loading
  useEffect(() => {
    isMountedRef.current = true
    initialAnimationRef.start(() => {
      if (!isMountedRef.current) return
      runBreathingCycle()

      Promise.all([onFontsLoaded, checkAuthStatus()])
        .then(() => {
          if (!isMountedRef.current) return
          console.log('[SplashAnimation] Fonts loaded and auth checked. Loading complete.')
          isLoadingCompleteRef.current = true
        })
        .catch((error) => {
          if (!isMountedRef.current) return
          console.error("[SplashAnimation] Font loading or auth check failed:", error)
          isLoadingCompleteRef.current = true
          triggerFinalNavigation()
        })
    })

    // Cleanup function
    return () => {
      isMountedRef.current = false
      initialAnimationRef.stop()
      currentAnimationRef.current?.stop()
    }
  }, [onFontsLoaded, initialAnimationRef, runBreathingCycle, checkAuthStatus, triggerFinalNavigation])

  return {
    animatedStyle: {
      opacity: opacityAnim,
      transform: [
        { scale: Animated.multiply(scaleAnim, breatheAnim) }
      ],
    },
  }
} 