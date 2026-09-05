import type { DetectedVoiceLanguage } from '../services/voiceService'

const isDev = import.meta.env.DEV

function log(label: string, ...args: unknown[]) {
  if (isDev) {
    // eslint-disable-next-line no-console
    console.log(`[Mira TTS] ${label}`, ...args)
  }
}

export function getBrowserSpeech(): SpeechSynthesis | null {
  if (typeof window === 'undefined') return null
  return window.speechSynthesis ?? null
}

export function selectVoice(
  voices: SpeechSynthesisVoice[],
  language: DetectedVoiceLanguage,
): SpeechSynthesisVoice | null {
  if (voices.length === 0) return null

  const targetLang = language === 'ur' ? 'ur' : 'en'
  const preferredLocale = language === 'ur' ? 'ur-pk' : 'en-us'

  const score = (voice: SpeechSynthesisVoice): number => {
    const voiceLang = voice.lang.toLowerCase().replace(/_/g, '-')
    if (voiceLang === preferredLocale) return 100
    if (voiceLang.startsWith(`${targetLang}-`)) return 80
    if (voiceLang.startsWith(targetLang)) return 60
    if (voiceLang.startsWith('en-')) return 40
    if (voiceLang.startsWith('en')) return 30
    if (voice.default) return 20
    return 0
  }

  const sorted = [...voices].sort((a, b) => score(b) - score(a))
  return sorted[0] ?? null
}

export function loadVoices(speech: SpeechSynthesis): Promise<SpeechSynthesisVoice[]> {
  const current = speech.getVoices()
  if (current.length > 0) return Promise.resolve(current)

  return new Promise((resolve) => {
    let resolved = false
    const handler = () => {
      if (resolved) return
      resolved = true
      speech.removeEventListener('voiceschanged', handler)
      resolve(speech.getVoices())
    }
    speech.addEventListener('voiceschanged', handler)
    // Some browsers fire the event before we attach; try again shortly.
    window.setTimeout(() => {
      if (!resolved) {
        const refreshed = speech.getVoices()
        if (refreshed.length > 0) handler()
      }
    }, 50)
    // Failsafe: do not block playback forever if voices never load.
    window.setTimeout(() => {
      if (!resolved) {
        resolved = true
        speech.removeEventListener('voiceschanged', handler)
        resolve(speech.getVoices())
      }
    }, 2000)
  })
}

export interface SpeakOptions {
  text: string
  language: DetectedVoiceLanguage
  voices?: SpeechSynthesisVoice[]
  onStart?: () => void
  onEnd?: () => void
  onError?: (error: string) => void
}

export async function speakBrowserText(options: SpeakOptions): Promise<boolean> {
  const { text, language, voices: providedVoices, onStart, onEnd, onError } = options
  const speech = getBrowserSpeech()
  if (!speech) {
    log('browser speech synthesis unavailable')
    return false
  }

  let available = providedVoices && providedVoices.length > 0 ? providedVoices : speech.getVoices()
  if (available.length === 0) {
    available = await loadVoices(speech)
  }

  const targetLang = language === 'ur' ? 'ur-PK' : 'en-US'
  const voice = selectVoice(available, language)

  log('speak', {
    language: targetLang,
    voiceCount: available.length,
    selectedVoice: voice?.name ?? 'none',
    selectedLang: voice?.lang ?? 'none',
  })

  return new Promise((resolve) => {
    speech.cancel()
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = targetLang
    if (voice) utterance.voice = voice

    utterance.onstart = () => {
      log('speech start')
      onStart?.()
    }
    utterance.onend = () => {
      log('speech end')
      onEnd?.()
      resolve(true)
    }
    utterance.onerror = (event) => {
      log('speech error', event.error)
      onError?.(event.error)
      resolve(false)
    }

    speech.speak(utterance)
  })
}
