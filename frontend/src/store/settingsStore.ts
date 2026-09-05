import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type Language = 'en' | 'ur'
export type Theme = 'dark' | 'light'

interface SettingsState {
  language: Language
  theme: Theme
  setLanguage: (lang: Language) => void
  toggleTheme: () => void
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set, get) => ({
      language: 'en',
      theme: 'dark',

      setLanguage: (language) => set({ language }),

      toggleTheme: () =>
        set({ theme: get().theme === 'dark' ? 'light' : 'dark' }),
    }),
    {
      name: 'healthos-settings',
    },
  ),
)
