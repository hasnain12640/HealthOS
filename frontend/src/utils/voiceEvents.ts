export type VoiceRefreshScope = 'dashboard' | 'womens_health'

const OPEN_EVENT = 'healthos:voice-open'
const REFRESH_EVENT = 'healthos:voice-refresh'

export function openVoiceAgent(): void {
  window.dispatchEvent(new Event(OPEN_EVENT))
}

export function onVoiceAgentOpen(listener: () => void): () => void {
  window.addEventListener(OPEN_EVENT, listener)
  return () => window.removeEventListener(OPEN_EVENT, listener)
}

export function dispatchVoiceRefresh(scopes: string[]): void {
  const refreshScopes = scopes.filter((scope): scope is VoiceRefreshScope =>
    scope === 'dashboard' || scope === 'womens_health',
  )
  if (refreshScopes.length) {
    window.dispatchEvent(new CustomEvent<VoiceRefreshScope[]>(REFRESH_EVENT, { detail: refreshScopes }))
  }
}

export function onVoiceRefresh(listener: (scopes: VoiceRefreshScope[]) => void): () => void {
  const handleEvent = (event: Event) => listener((event as CustomEvent<VoiceRefreshScope[]>).detail)
  window.addEventListener(REFRESH_EVENT, handleEvent)
  return () => window.removeEventListener(REFRESH_EVENT, handleEvent)
}
