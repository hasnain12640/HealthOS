import { Mic } from 'lucide-react'
import { useT } from '../../i18n/useT'
import { openVoiceAgent } from '../../utils/voiceEvents'

interface VoiceAgentTriggerProps {
  compact?: boolean
  className?: string
}

export function VoiceAgentTrigger({ compact = false, className = '' }: VoiceAgentTriggerProps) {
  const t = useT()

  return (
    <button
      type="button"
      onClick={openVoiceAgent}
      className={[
        'inline-flex items-center justify-center gap-2 rounded-lg border border-primary/40 bg-primary/10 text-primary transition-colors hover:bg-primary/20',
        compact ? 'h-11 w-11 rounded-full' : 'px-3 py-2 text-sm font-medium',
        className,
      ].join(' ')}
      aria-label={t['voice.open']}
      title={t['voice.open']}
    >
      <Mic size={compact ? 18 : 15} />
      {!compact && <span>{t['voice.open']}</span>}
    </button>
  )
}
