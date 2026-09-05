import { useSettingsStore } from '../store/settingsStore'
import { en, ur, type TranslationDict } from './translations'

const dictionaries: Record<string, TranslationDict> = { en, ur }

export function useT(): TranslationDict {
  const language = useSettingsStore((s) => s.language)
  return dictionaries[language] ?? en
}
