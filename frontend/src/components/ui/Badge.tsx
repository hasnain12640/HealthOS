type BadgeVariant = 'normal' | 'low' | 'high' | 'critical' | 'info' | 'default'

interface BadgeProps {
  label: string
  variant?: BadgeVariant
  size?: 'sm' | 'md'
}

const variantConfig: Record<BadgeVariant, { dot: string; text: string; bg: string }> = {
  normal:   { dot: 'bg-status-normal', text: 'text-status-normal', bg: 'bg-status-normal/10' },
  low:      { dot: 'bg-status-low', text: 'text-status-low', bg: 'bg-status-low/10' },
  high:     { dot: 'bg-status-high', text: 'text-status-high', bg: 'bg-status-high/10' },
  critical: { dot: 'bg-status-critical', text: 'text-status-critical', bg: 'bg-status-critical/10' },
  info:     { dot: 'bg-primary', text: 'text-primary', bg: 'bg-primary/10' },
  default:  { dot: 'bg-text-muted', text: 'text-text-secondary', bg: 'bg-bg-elevated' },
}

const labelMap: Record<BadgeVariant, string> = {
  normal: 'Normal', low: 'Low', high: 'High', critical: 'Critical',
  info: 'Info', default: '',
}

export function Badge({ label, variant = 'default', size = 'sm' }: BadgeProps) {
  const cfg = variantConfig[variant]
  const displayLabel = label || labelMap[variant]
  return (
    <span
      className={[
        'inline-flex items-center gap-1.5 rounded-full font-medium',
        cfg.bg, cfg.text,
        size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm',
      ].join(' ')}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
      {displayLabel}
    </span>
  )
}

export function StatusBadge({ status }: { status: 'normal' | 'low' | 'high' | 'critical' }) {
  return <Badge label={status.charAt(0).toUpperCase() + status.slice(1)} variant={status} />
}
