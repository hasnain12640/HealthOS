import { useState } from 'react'
import { Menu, Bell, Search } from 'lucide-react'
import { useT } from '../../i18n/useT'

interface TopBarProps {
  onMenuToggle: () => void
}

export function TopBar({ onMenuToggle }: TopBarProps) {
  const [searchValue, setSearchValue] = useState('')
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

      {/* Search bar */}
      <div className="hidden sm:flex items-center gap-2 bg-bg-surface border border-border rounded-lg px-3 py-1.5 w-64">
        <Search size={14} className="text-text-muted shrink-0" />
        <input
          type="text"
          value={searchValue}
          onChange={e => setSearchValue(e.target.value)}
          placeholder={t['topbar.search_placeholder']}
          className="bg-transparent text-sm text-text-primary placeholder-text-muted outline-none w-full"
        />
      </div>

      {/* Right: status pill + notification */}
      <div className="flex items-center gap-3">
        <div className="hidden sm:flex items-center gap-1.5 bg-accent/10 border border-accent/20 rounded-full px-3 py-1">
          <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
          <span className="text-accent text-xs font-medium">{t['topbar.ai_ready']}</span>
        </div>
        <button className="p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-bg-surface transition-colors relative">
          <Bell size={16} />
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-primary" />
        </button>
      </div>
    </header>
  )
}
