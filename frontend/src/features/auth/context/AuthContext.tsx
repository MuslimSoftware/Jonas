import React, { createContext, useContext, useEffect, useState } from 'react'
import { useRouter } from 'expo-router'
import {
  saveAccessToken,
  saveRefreshToken,
  getAccessToken,
  getRefreshToken,
  deleteAccessToken,
  deleteRefreshToken,
} from '@/config/storage.config'

type AuthContextType = {
  isAuthenticated: boolean
  isLoading: boolean
  accessToken: string | null
  signIn: (access: string, refresh: string) => Promise<void>
  signOut: () => Promise<void>
  checkAuthStatus: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isLoading, setIsLoading] = useState(true)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const router = useRouter()

  const checkAuthStatus = async () => {
    setIsLoading(true)
    try {
      const [storedAccessToken, storedRefreshToken] = await Promise.all([
        getAccessToken(),
        getRefreshToken(),
      ])

      if (storedAccessToken && storedRefreshToken) {
        setAccessToken(storedAccessToken)
        setIsAuthenticated(true)
      } else {
        setAccessToken(null)
        setIsAuthenticated(false)
      }
    } catch (e) {
      console.error("Error checking auth status:", e)
      setAccessToken(null)
      setIsAuthenticated(false)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    checkAuthStatus()
  }, [])

  const signIn = async (access: string, refresh: string) => {
    setIsLoading(true)
    try {
      await Promise.all([
        saveAccessToken(access),
        saveRefreshToken(refresh),
      ])
      setAccessToken(access)
      setIsAuthenticated(true)
      router.replace('/chat')
    } catch (e) {
      console.error("Error signing in:", e)
    } finally {
      setIsLoading(false)
    }
  }

  const signOut = async () => {
    setIsLoading(true)
    try {
      await Promise.all([
        deleteAccessToken(),
        deleteRefreshToken(),
      ])
      setAccessToken(null)
      setIsAuthenticated(false)
      router.replace('/(auth)/landing')
    } catch (e) {
      console.error("Error signing out:", e)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        isLoading,
        accessToken,
        signIn,
        signOut,
        checkAuthStatus
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
