import { useCallback, useEffect, useState } from 'react'
import { AlertTriangle, Check, LoaderCircle, Mic, Square, Volume2, X } from 'lucide-react'
import { useVoiceAgent } from '../../hooks/useVoiceAgent'
import { useT } from '../../i18n/useT'
import { useSettingsStore } from '../../store/settingsStore'
import { useAuthStore } from '../../store/authStore'
import type { VoiceCommandResult, VoiceLanguage } from '../../services/voiceService'
import { dispatchVoiceRefresh, onVoiceAgentOpen } from '../../utils/voiceEvents'
import { Button } from '../ui'
import { VoiceAgentTrigger } from './VoiceAgentTrigger'

function intentLabel(intent: string): string {
  return intent.replaceAll('_', ' ').replace(/\b\w/g, character => character.toUpperCase())
}

export function VoiceAgentHost() {
  const t = useT()
  const profile = useAuthStore(state => state.profile)
  const settingsLanguage = useSettingsStore(state => state.language)
  const [open, setOpen] = useState(false)
  const [languageOverride, setLanguageOverride] = useState<VoiceLanguage | null>(null)
  const languageHint = languageOverride ?? (settingsLanguage === 'ur' ? 'ur' : 'auto')
  const [useBrowserRecognition, setUseBrowserRecognition] = useState(true)

  useEffect(() => onVoiceAgentOpen(() => setOpen(true)), [])

  const handleCommand = useCallback((command: VoiceCommandResult) => {
    dispatchVoiceRefresh(command.refresh_scopes)
  }, [])

  const {
    stage,
    transcript,
    command,
    error,
    micError,
    recognitionSupported,
    startRecording,
    stopRecording,
    cancel,
    confirm,
    replayResponse,
    stopSpeaking,
  } = useVoiceAgent({ languageHint, useBrowserRecognition, onCommand: handleCommand })

  if (!profile) return null

  const listening = stage === 'listening'
  const working = stage === 'processing' || stage === 'updating'
  const close = () => {
    cancel()
    setOpen(false)
  }

  const micErrorMessage = micError
    ? t[
        micError === 'permission_denied'
          ? 'voice.microphone_blocked'
          : micError === 'not_found'
            ? 'voice.microphone_not_found'
            : micError === 'unsupported'
              ? 'voice.microphone_unavailable'
              : 'voice.microphone_generic'
      ]
    : error

  const micErrorRecoverable = micError === 'permission_denied' || micError === 'not_found' || micError === 'generic'

  const stageText = listening
    ? t['voice.listening']
    : stage === 'processing'
      ? t['voice.processing']
      : stage === 'updating'
        ? t['voice.updating']
        : stage === 'speaking'
          ? t['voice.speaking']
          : stage === 'error' && micError
            ? t['voice.microphone_issue']
            : stage === 'error'
              ? t['voice.error']
              : t['voice.ready']

  return (
    <>
      {open && (
        <div className="fixed inset-0 z-50 bg-black/30 sm:bg-transparent" onMouseDown={close}>
          <section
            role="dialog"
            aria-modal="true"
            aria-labelledby="voice-agent-title"
            onMouseDown={event => event.stopPropagation()}
            className="fixed inset-x-3 bottom-3 max-h-[calc(100dvh-1.5rem)] overflow-y-auto rounded-2xl border border-border bg-bg-surface p-4 shadow-2xl sm:inset-x-auto sm:bottom-5 sm:end-5 sm:w-[25rem]"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 id="voice-agent-title" className="text-text-primary text-sm font-semibold">{t['voice.title']}</h2>
                <p className="text-text-secondary text-xs mt-1">{t['voice.subtitle']}</p>
              </div>
              <button type="button" onClick={close} className="rounded-lg p-1.5 text-text-muted hover:bg-bg-elevated hover:text-text-primary" aria-label={t['voice.close']}>
                <X size={16} />
              </button>
            </div>

            <div className="mt-4 grid grid-cols-2 gap-3">
              <label className="block">
                <span className="text-text-secondary text-xs">{t['voice.language']}</span>
                <select
                  value={languageHint}
                  disabled={listening || working}
                  onChange={event => setLanguageOverride(event.target.value as VoiceLanguage)}
                  className="mt-1.5 w-full rounded-lg border border-border bg-bg-elevated px-2.5 py-2 text-sm text-text-primary outline-none focus:border-primary disabled:opacity-50"
                >
                  <option value="auto">{t['voice.language_auto']}</option>
                  <option value="en">{t['voice.language_en']}</option>
                  <option value="ur">{t['voice.language_ur']}</option>
                </select>
              </label>
              <label className="flex cursor-pointer items-center gap-2 rounded-lg border border-border bg-bg-elevated px-2.5 py-2 text-xs text-text-secondary">
                <input
                  type="checkbox"
                  checked={useBrowserRecognition}
                  disabled={listening || working}
                  onChange={event => setUseBrowserRecognition(event.target.checked)}
                  className="accent-primary"
                />
                <span>{t['voice.browser_transcription']}</span>
              </label>
            </div>
            {useBrowserRecognition && !recognitionSupported && (
              <p className="mt-2 text-warning text-xs">{t['voice.recognition_unavailable']}</p>
            )}

            <div className="mt-4 rounded-xl border border-border bg-bg-base p-4 text-center">
              <p className="text-text-secondary text-xs" aria-live="polite">{stageText}</p>
              <button
                type="button"
                disabled={working || stage === 'speaking'}
                onClick={() => { if (listening) stopRecording(); else void startRecording() }}
                className={[
                  'mx-auto mt-3 flex h-16 w-16 items-center justify-center rounded-full border transition-colors disabled:cursor-not-allowed disabled:opacity-50',
                  listening ? 'border-danger/60 bg-danger/15 text-danger animate-pulse' : 'border-primary/50 bg-primary/15 text-primary hover:bg-primary/25',
                ].join(' ')}
                aria-label={listening ? t['voice.stop'] : t['voice.start']}
              >
                {working ? <LoaderCircle size={23} className="animate-spin" /> : listening ? <Square size={20} fill="currentColor" /> : <Mic size={23} />}
              </button>
              <p className="mt-2 text-text-muted text-[11px]">{listening ? t['voice.tap_to_stop'] : t['voice.tap_to_talk']}</p>
            </div>

            {transcript && (
              <div className="mt-3 rounded-lg bg-bg-elevated p-3">
                <p className="text-text-muted text-[10px] uppercase tracking-wide">{t['voice.transcript']}</p>
                <p className="mt-1 text-text-primary text-sm leading-relaxed">{transcript}</p>
              </div>
            )}

            {command && (
              <div className="mt-3 rounded-lg border border-primary/20 bg-primary/5 p-3">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-primary text-xs font-medium">{intentLabel(command.intent)}</p>
                  <span className="text-text-muted text-[10px]">{command.provider === 'qwen' ? 'Qwen' : 'HealthOS'}</span>
                </div>
                <p className="mt-2 text-text-primary text-sm leading-relaxed">{command.response_text}</p>
                {command.result && (
                  <pre className="mt-2 max-h-24 overflow-auto whitespace-pre-wrap rounded bg-bg-base p-2 text-text-secondary text-[11px]">{JSON.stringify(command.result, null, 2)}</pre>
                )}
                {(stage === 'response' || stage === 'speaking') && (
                  <div className="mt-2 inline-flex items-center gap-2">
                    {stage === 'speaking' ? (
                      <>
                        <LoaderCircle size={13} className="animate-spin text-primary" />
                        <span className="text-text-secondary text-xs">{t['voice.playing_response']}</span>
                        <button
                          type="button"
                          onClick={() => void stopSpeaking()}
                          className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-danger text-xs hover:bg-danger/10"
                        >
                          <Square size={12} fill="currentColor" /> {t['voice.stop_speech']}
                        </button>
                      </>
                    ) : (
                      <button
                        type="button"
                        onClick={() => void replayResponse()}
                        className="inline-flex items-center gap-1 text-primary text-xs hover:underline"
                      >
                        <Volume2 size={13} /> {t['voice.replay']}
                      </button>
                    )}
                  </div>
                )}
              </div>
            )}

            {stage === 'confirmation' && command?.confirmation_token && (
              <div className="mt-3 flex gap-2">
                <Button size="sm" onClick={() => void confirm()}><Check size={14} />{t['voice.confirm']}</Button>
                <Button size="sm" variant="ghost" onClick={cancel}>{t['voice.cancel']}</Button>
              </div>
            )}

            {micErrorMessage && (
              <div className="mt-3 rounded-lg border border-danger/30 bg-danger/10 p-3 text-danger text-xs">
                <div className="flex items-start gap-2">
                  <AlertTriangle size={15} className="mt-0.5 shrink-0" />
                  <p>{micErrorMessage}</p>
                </div>
                {micErrorRecoverable && (
                  <Button
                    size="sm"
                    className="mt-2"
                    onClick={() => void startRecording()}
                    disabled={working || stage === 'speaking'}
                  >
                    {t['voice.try_again']}
                  </Button>
                )}
              </div>
            )}
          </section>
        </div>
      )}
      <div className="fixed bottom-5 end-5 z-40">
        <VoiceAgentTrigger compact className="shadow-lg" />
      </div>
    </>
  )
}
