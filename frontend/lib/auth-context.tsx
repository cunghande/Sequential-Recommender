"use client"

import React, { createContext, useContext, useState, useEffect } from "react"
import { api } from "./api"

interface User {
  user_id: string
  email: string
  full_name?: string
  avatar_url?: string // Placeholder for UI
}

interface AuthContextType {
  user: User | null
  token: string | null
  login: (token: string, user: User) => void
  logout: () => void
  updateUser: (user: Partial<User>) => void
  guestId: string
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [guestId, setGuestId] = useState<string>("")
  const [isLoaded, setIsLoaded] = useState(false)

  useEffect(() => {
    // Load from local storage on mount
    const storedToken = localStorage.getItem("nexus_token")
    const storedUser = localStorage.getItem("nexus_user")
    
    if (storedToken && storedUser) {
      setToken(storedToken)
      try {
        setUser(JSON.parse(storedUser))
      } catch (e) {
        console.error("Failed to parse stored user", e)
      }
    }
    
    let gid = localStorage.getItem("nexus_guest_id")
    if (!gid) {
      gid = "guest_" + Math.random().toString(36).substr(2, 9)
      localStorage.setItem("nexus_guest_id", gid)
    }
    setGuestId(gid)

    setIsLoaded(true)
  }, [])

  const login = (newToken: string, newUser: User) => {
    setToken(newToken)
    setUser(newUser)
    localStorage.setItem("nexus_token", newToken)
    localStorage.setItem("nexus_user", JSON.stringify(newUser))
  }

  const logout = () => {
    if (token) {
      api.post('/auth/logout', {}).catch(() => {})
    }
    setToken(null)
    setUser(null)
    localStorage.removeItem("nexus_token")
    localStorage.removeItem("nexus_user")
  }

  const updateUser = (updatedFields: Partial<User>) => {
    if (user) {
      const newUser = { ...user, ...updatedFields }
      setUser(newUser)
      localStorage.setItem("nexus_user", JSON.stringify(newUser))
    }
  }

  if (!isLoaded) return null // Prevent hydration mismatch

  return (
    <AuthContext.Provider value={{ user, token, login, logout, updateUser, guestId }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
