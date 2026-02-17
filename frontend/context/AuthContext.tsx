'use client'

import React, { createContext, useContext, useState, useEffect } from 'react'
import { authApi } from '@/lib/api'
import toast from 'react-hot-toast'
import { useRouter } from 'next/navigation'

interface User {
  id: string
  email: string
  full_name: string
  is_active: boolean
  created_at: string
}

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, fullName: string) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  // Load user on mount
  useEffect(() => {
    const token = localStorage.getItem('access_token')
    const savedUser = localStorage.getItem('user')
    
    if (token && savedUser) {
      try {
        setUser(JSON.parse(savedUser))
        // Verify token is still valid
        authApi.getProfile()
          .then(userData => {
            setUser(userData)
            localStorage.setItem('user', JSON.stringify(userData))
          })
          .catch(() => {
            // Token expired or invalid
            localStorage.removeItem('access_token')
            localStorage.removeItem('user')
            setUser(null)
          })
          .finally(() => setLoading(false))
      } catch {
        setLoading(false)
      }
    } else {
      setLoading(false)
    }
  }, [])

  const login = async (email: string, password: string) => {
    try {
      const data = await authApi.login(email, password)
      localStorage.setItem('access_token', data.access_token)
      
      // Get user profile
      const userData = await authApi.getProfile()
      setUser(userData)
      localStorage.setItem('user', JSON.stringify(userData))
      
      toast.success('Welcome back!')
      router.push('/dashboard')
    } catch (error: any) {
      throw error
    }
  }

  const register = async (email: string, password: string, fullName: string) => {
    try {
      await authApi.register({
        email,
        password,
        full_name: fullName,
      })
      
      // Auto login after registration
      await login(email, password)
      toast.success('Account created successfully!')
    } catch (error: any) {
      throw error
    }
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    setUser(null)
    toast.success('Logged out successfully')
    router.push('/login')
  }

  const refreshUser = async () => {
    try {
      const userData = await authApi.getProfile()
      setUser(userData)
      localStorage.setItem('user', JSON.stringify(userData))
    } catch (error) {
      console.error('Failed to refresh user:', error)
    }
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser }}>
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
