type BadgeVariant = 'normal' | 'low' | 'high' | 'critical' | 'info' | 'default'

interface BadgeProps {
  label: string
  variant?: BadgeVariant
  size?: 'sm' | 'md'
}

const variantConfig: Record<BadgeVariant, { dot: string; text: string; bg: string }> = {
  normal:   { dot: 'bg-[#10B981]', text: 'text-[#10B981]', bg: 'bg-[#10B981]/10' },
  low:      { dot: 'bg-[#F59E0B]', text: 'text-[#F59E0B]', bg: 'bg-[#F59E0B]/10' },
  high:     { dot: 'bg-[#EF4444]', text: 'text-[#EF4444]', bg: 'bg-[#EF4444]/10' },
  critical: { dot: 'bg-[#DC2626]', text: 'text-[#DC2626]', bg: 'bg-[#DC2626]/10' },
  info:     { dot: 'bg-[#0EA5E9]', text: 'text-[#0EA5E9]', bg: 'bg-[#0EA5E9]/10' },
  default:  { dot: 'bg-[#6B7280]', text: 'text-[#9CA3AF]', bg: 'bg-[#1F2937]' },
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
