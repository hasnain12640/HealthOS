import api from './api'

export type VoiceLanguage = 'auto' | 'en' | 'ur'
export type DetectedVoiceLanguage = Exclude<VoiceLanguage, 'auto'>
export type VoiceAction = 'answered' | 'executed' | 'confirmation_required' | 'clarification_required' | 'unavailable'

export interface VoiceTranscription {
  transcript: string
  language: DetectedVoiceLanguage
  provider: string
}

export interface VoiceCommandResult {
  transcript: string
  language: DetectedVoiceLanguage
  intent: string
  action: VoiceAction
  requires_confirmation: boolean
  confirmation_token: string | null
  result: Record<string, unknown> | null
  response_text: string
  provider: string
  refresh_scopes: string[]
}

export interface VoiceCommandInput {
  audio: Blob
  languageHint: VoiceLanguage
  browserTranscript?: string
}

export interface SpeakFallback {
  mode: 'browser_fallback'
  text: string
  language: DetectedVoiceLanguage
  provider: string
}

export interface SpeakAudio {
  mode: 'audio'
  audio: Blob
  mediaType: string
  provider: string
}

function commandForm({ audio, languageHint, browserTranscript }: VoiceCommandInput): FormData {
  const form = new FormData()
  form.append('audio', audio, 'voice.webm')
  form.append('language_hint', languageHint)
  if (browserTranscript?.trim()) form.append('browser_transcript', browserTranscript.trim())
  return form
}

export async function transcribeVoice(input: VoiceCommandInput): Promise<VoiceTranscription> {
  const { data } = await api.post<VoiceTranscription>('/voice/transcribe', commandForm(input), {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function sendVoiceCommand(input: VoiceCommandInput): Promise<VoiceCommandResult> {
  const { data } = await api.post<VoiceCommandResult>('/voice/command', commandForm(input), {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function confirmVoiceCommand(confirmationToken: string): Promise<VoiceCommandResult> {
  const form = new FormData()
  form.append('confirmation_token', confirmationToken)
  form.append('confirm', 'true')
  const { data } = await api.post<VoiceCommandResult>('/voice/command', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function speakVoice(text: string, language: DetectedVoiceLanguage): Promise<SpeakFallback | SpeakAudio> {
  const response = await api.post<Blob>('/voice/speak', { text, language }, { responseType: 'blob' })
  const mediaType = String(response.headers['content-type'] ?? '').toLowerCase()

  if (mediaType.includes('application/json')) {
    return JSON.parse(await response.data.text()) as SpeakFallback
  }

  return {
    mode: 'audio',
    audio: response.data,
    mediaType: mediaType || 'audio/mpeg',
    provider: String(response.headers['x-voice-provider'] ?? 'qwen'),
  }
}
