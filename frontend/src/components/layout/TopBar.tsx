import { Menu } from 'lucide-react'
import { useT } from '../../i18n/useT'

interface TopBarProps {
  onMenuToggle: () => void
}

export function TopBar({ onMenuToggle }: TopBarProps) {
  const t = useT()

  return (
    <header className="h-14 flex items-center justify-between px-4 border-b border-border bg-bg-base shrink-0">
      {/* Left: hamburger (mobile) */}
      <button
        onClick={onMenuToggle}
        className="lg:hidden p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-bg-surface transition-colors"
        aria-label="Open menu"
      >
        <Menu size={18} />
      </button>

      {/* Page title spacer keeps the AI status pill right-aligned */}
      <div className="flex-1" />

      {/* Right: AI-ready status pill */}
      <div className="hidden sm:flex items-center gap-1.5 bg-accent/10 border border-accent/20 rounded-full px-3 py-1">
        <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
        <span className="text-accent text-xs font-medium">{t['topbar.ai_ready']}</span>
      </div>
    </header>
  )
}
