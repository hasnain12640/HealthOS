import { useCallback, useEffect, useRef, useState } from 'react'
import {
  confirmVoiceCommand,
  sendVoiceCommand,
  speakVoice,
  type DetectedVoiceLanguage,
  type VoiceCommandResult,
  type VoiceLanguage,
} from '../services/voiceService'
import { getBrowserSpeech, loadVoices, speakBrowserText } from '../utils/browserSpeech'

type VoiceStage = 'idle' | 'listening' | 'processing' | 'updating' | 'response' | 'confirmation' | 'speaking' | 'error'

type MicErrorType = 'permission_denied' | 'not_found' | 'unsupported' | 'generic' | null

interface BrowserRecognitionResult {
  readonly transcript: string
}

interface BrowserRecognitionResultList {
  readonly length: number
  [index: number]: { readonly 0: BrowserRecognitionResult }
}

interface BrowserRecognitionEvent extends Event {
  readonly resultIndex: number
  readonly results: BrowserRecognitionResultList
}

interface BrowserRecognition {
  lang: string
  interimResults: boolean
  continuous: boolean
  maxAlternatives: number
  onresult: ((event: BrowserRecognitionEvent) => void) | null
  onerror: ((event: Event) => void) | null
  onend: (() => void) | null
  start: () => void
  stop: () => void
  abort: () => void
}

type BrowserRecognitionConstructor = new () => BrowserRecognition

declare global {
  interface Window {
    SpeechRecognition?: BrowserRecognitionConstructor
    webkitSpeechRecognition?: BrowserRecognitionConstructor
  }
}

interface UseVoiceAgentOptions {
  languageHint: VoiceLanguage
  useBrowserRecognition: boolean
  onCommand: (command: VoiceCommandResult) => void
}

function errorMessage(error: unknown): string {
  const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if ((error as { message?: string })?.message === 'Failed to fetch') return 'Unable to reach the voice service.'
  return 'Voice processing is temporarily unavailable. Please try again.'
}

function recognitionConstructor(): BrowserRecognitionConstructor | null {
  return window.SpeechRecognition ?? window.webkitSpeechRecognition ?? null
}

export function useVoiceAgent({ languageHint, useBrowserRecognition, onCommand }: UseVoiceAgentOptions) {
  const [stage, setStage] = useState<VoiceStage>('idle')
  const [transcript, setTranscript] = useState('')
  const [command, setCommand] = useState<VoiceCommandResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [micError, setMicError] = useState<MicErrorType>(null)
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([])
  const [recognitionSupported, setRecognitionSupported] = useState(() => Boolean(recognitionConstructor()))
  const recorderRef = useRef<MediaRecorder | null>(null)
  const recognitionRef = useRef<BrowserRecognition | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const transcriptRef = useRef('')
  const discardRecordingRef = useRef(false)
  const audioRef = useRef<HTMLAudioElement | null>(null)

  const releaseStream = useCallback(() => {
    streamRef.current?.getTracks().forEach(track => track.stop())
    streamRef.current = null
  }, [])

  const stopSpeech = useCallback(() => {
    audioRef.current?.pause()
    audioRef.current = null
    window.speechSynthesis?.cancel()
  }, [])

  const playBrowserSpeech = useCallback(async (text: string, language: DetectedVoiceLanguage) => {
    await speakBrowserText({ text, language, voices })
  }, [voices])

  const playAudio = useCallback((audio: Blob) => {
    return new Promise<void>((resolve) => {
      const source = URL.createObjectURL(audio)
      const player = new Audio(source)
      audioRef.current = player
      const finish = () => {
        URL.revokeObjectURL(source)
        if (audioRef.current === player) audioRef.current = null
        resolve()
      }
      player.onended = finish
      player.onerror = finish
      void player.play().catch(finish)
    })
  }, [])

  const speakResponse = useCallback(async (response: VoiceCommandResult) => {
    if (!response.response_text) {
      setStage('response')
      return
    }

    stopSpeech()
    setStage('speaking')
    try {
      const speech = await speakVoice(response.response_text, response.language)
      if (speech.mode === 'audio') await playAudio(speech.audio)
      else await playBrowserSpeech(speech.text, speech.language)
    } catch {
      // A completed command remains visible even when speech output is unavailable.
    } finally {
      setStage('response')
    }
  }, [playAudio, playBrowserSpeech, stopSpeech])

  const receiveCommand = useCallback(async (response: VoiceCommandResult) => {
    setCommand(response)
    onCommand(response)
    if (response.requires_confirmation) {
      setStage('confirmation')
      return
    }
    await speakResponse(response)
  }, [onCommand, speakResponse])

  const processRecording = useCallback(async (audio: Blob) => {
    setStage('processing')
    try {
      const response = await sendVoiceCommand({
        audio,
        languageHint,
        browserTranscript: useBrowserRecognition ? transcriptRef.current : undefined,
      })
      await receiveCommand(response)
    } catch (err) {
      setError(errorMessage(err))
      setStage('error')
    }
  }, [languageHint, receiveCommand, useBrowserRecognition])

  const startRecognition = useCallback(() => {
    if (!useBrowserRecognition) return
    const Recognition = recognitionConstructor()
    setRecognitionSupported(Boolean(Recognition))
    if (!Recognition) return

    const recognition = new Recognition()
    recognition.lang = languageHint === 'ur' ? 'ur-PK' : 'en-PK'
    recognition.interimResults = true
    recognition.continuous = false
    recognition.maxAlternatives = 1
    recognition.onresult = (event) => {
      let nextTranscript = transcriptRef.current
      for (let index = event.resultIndex; index < event.results.length; index += 1) {
        nextTranscript += `${nextTranscript ? ' ' : ''}${event.results[index][0].transcript}`
      }
      transcriptRef.current = nextTranscript.trim()
      setTranscript(transcriptRef.current)
    }
    recognition.onerror = () => {
      setRecognitionSupported(false)
      recognitionRef.current = null
    }
    recognitionRef.current = recognition
    try {
      recognition.start()
    } catch {
      setRecognitionSupported(false)
      recognitionRef.current = null
    }
  }, [languageHint, useBrowserRecognition])

  const startRecording = useCallback(async () => {
    if (stage === 'listening' || stage === 'processing' || stage === 'updating') return
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
      setMicError('unsupported')
      setError('Your browser does not support microphone recording.')
      setStage('error')
      return
    }

    setError(null)
    setMicError(null)
    setCommand(null)
    setTranscript('')
    transcriptRef.current = ''
    discardRecordingRef.current = false

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream
      const mimeType = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg']
        .find(type => MediaRecorder.isTypeSupported(type))
      const recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream)
      recorderRef.current = recorder
      chunksRef.current = []
      recorder.ondataavailable = (event) => {
        if (event.data.size) chunksRef.current.push(event.data)
      }
      recorder.onstop = () => {
        recorderRef.current = null
        releaseStream()
        if (discardRecordingRef.current) return
        const audio = new Blob(chunksRef.current, { type: recorder.mimeType || 'audio/webm' })
        chunksRef.current = []
        if (!audio.size) {
          setMicError('generic')
          setError('The recording was empty. Please try again.')
          setStage('error')
          return
        }
        void processRecording(audio)
      }
      recorder.start(250)
      startRecognition()
      setStage('listening')
    } catch (err) {
      releaseStream()
      const name = (err as { name?: string })?.name
      if (name === 'NotAllowedError' || name === 'PermissionDeniedError') {
        setMicError('permission_denied')
        setError('Microphone access is blocked. Allow microphone access for this site, then try again.')
      } else if (name === 'NotFoundError' || name === 'DevicesNotFoundError') {
        setMicError('not_found')
        setError('No microphone found. Please connect a microphone and try again.')
      } else {
        setMicError('generic')
        setError('Unable to start microphone recording. Please check your microphone and try again.')
      }
      setStage('error')
    }
  }, [processRecording, releaseStream, stage, startRecognition])

  const stopRecording = useCallback(() => {
    if (stage !== 'listening') return
    recognitionRef.current?.stop()
    recognitionRef.current = null
    recorderRef.current?.stop()
  }, [stage])

  const cancel = useCallback(() => {
    discardRecordingRef.current = true
    recognitionRef.current?.abort()
    recognitionRef.current = null
    recorderRef.current?.stop()
    recorderRef.current = null
    releaseStream()
    stopSpeech()
    setTranscript('')
    transcriptRef.current = ''
    setCommand(null)
    setError(null)
    setMicError(null)
    setStage('idle')
  }, [releaseStream, stopSpeech])

  const confirm = useCallback(async () => {
    const token = command?.confirmation_token
    if (!token) return
    setError(null)
    setStage('updating')
    try {
      await receiveCommand(await confirmVoiceCommand(token))
    } catch (err) {
      setError(errorMessage(err))
      setStage('error')
    }
  }, [command?.confirmation_token, receiveCommand])

  const stopSpeaking = useCallback(() => {
    stopSpeech()
    setStage('response')
  }, [stopSpeech])

  const replayResponse = useCallback(() => {
    if (command) void speakResponse(command)
  }, [command, speakResponse])

  // Load and keep browser TTS voices up to date. Chrome often starts with an empty list
  // and populates it asynchronously via the voiceschanged event.
  useEffect(() => {
    const speech = getBrowserSpeech()
    if (!speech) return undefined

    const refresh = () => {
      const list = speech.getVoices()
      setVoices(list)
      if (import.meta.env.DEV && list.length > 0) {
        // eslint-disable-next-line no-console
        console.log('[Mira TTS] voices updated', list.length, list.map(v => `${v.name} (${v.lang})`).slice(0, 5))
      }
    }

    void loadVoices(speech).then(refresh)
    speech.addEventListener('voiceschanged', refresh)
    return () => speech.removeEventListener('voiceschanged', refresh)
  }, [])

  useEffect(() => () => {
    discardRecordingRef.current = true
    recognitionRef.current?.abort()
    recorderRef.current?.stop()
    releaseStream()
    stopSpeech()
  }, [releaseStream, stopSpeech])

  return {
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
  }
}
