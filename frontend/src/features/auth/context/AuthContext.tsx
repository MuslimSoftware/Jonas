import React, { createContext, useContext, useState } from 'react'
import { router } from 'expo-router'

type AuthContextType = {
  isAuthenticated: boolean
  signIn: () => void
  signOut: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  const signIn = () => {
    setIsAuthenticated(true)
    router.replace('/(main)')
  }

  const signOut = () => {
    setIsAuthenticated(false)
    router.replace('/(auth)/landing')
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, signIn, signOut }}>
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
