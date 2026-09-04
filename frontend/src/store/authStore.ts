import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { login as apiLogin, register as apiRegister, getMe, logout as apiLogout } from '../services/authService'
import { getProfile } from '../services/profileService'
import type { User } from '../services/authService'
import type { ProfileData } from '../services/profileService'

async function _safeGetProfile(): Promise<ProfileData | null> {
  try {
    return await getProfile()
  } catch (err: unknown) {
    const status = (err as { response?: { status?: number } })?.response?.status
    if (status === 404) {
      return null
    }
    throw err
  }
}

interface AuthState {
  token: string | null
  user: User | null
  profile: ProfileData | null
  loading: boolean
  bootstrapped: boolean

  setToken: (token: string | null) => void
  setUser: (user: User | null) => void
  setProfile: (profile: ProfileData | null) => void
  setLoading: (loading: boolean) => void
  setBootstrapped: (bootstrapped: boolean) => void

  login: (email: string, password: string) => Promise<void>
  register: (name: string, email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  bootstrap: () => Promise<void>
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      profile: null,
      loading: false,
      bootstrapped: false,

      setToken: (token) => set({ token }),
      setUser: (user) => set({ user }),
      setProfile: (profile: ProfileData | null) => set({ profile }),
      setLoading: (loading) => set({ loading }),
      setBootstrapped: (bootstrapped) => set({ bootstrapped }),

      login: async (email, password) => {
        set({ loading: true })
        try {
          const data = await apiLogin({ email, password })
          localStorage.setItem('healthos_token', data.access_token)
          const profile = await _safeGetProfile()
          set({ token: data.access_token, user: data.user, profile, loading: false })
        } catch (error) {
          set({ loading: false })
          throw error
        }
      },

      register: async (name, email, password) => {
        set({ loading: true })
        try {
          const data = await apiRegister({ name, email, password })
          localStorage.setItem('healthos_token', data.access_token)
          set({ token: data.access_token, user: data.user, profile: null, loading: false })
        } catch (error) {
          set({ loading: false })
          throw error
        }
      },

      logout: async () => {
        try {
          await apiLogout()
        } finally {
          localStorage.removeItem('healthos_token')
          set({ token: null, user: null, profile: null, bootstrapped: true })
        }
      },

      bootstrap: async () => {
        const token = localStorage.getItem('healthos_token')
        if (!token) {
          set({ token: null, user: null, profile: null, bootstrapped: true })
          return
        }

        set({ token, loading: true })
        try {
          const user = await getMe()
          const profile = await _safeGetProfile()
          set({ user, profile, loading: false, bootstrapped: true })
        } catch {
          localStorage.removeItem('healthos_token')
          set({ token: null, user: null, profile: null, loading: false, bootstrapped: true })
        }
      },
    }),
    {
      name: 'healthos-auth',
      partialize: (state) => ({ token: state.token }),
    }
  )
)
