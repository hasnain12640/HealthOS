import { useState } from 'react'
import { Menu, Bell, Search } from 'lucide-react'

interface TopBarProps {
  onMenuToggle: () => void
}

export function TopBar({ onMenuToggle }: TopBarProps) {
  const [searchValue, setSearchValue] = useState('')

  return (
    <header className="h-14 flex items-center justify-between px-4 border-b border-[#1F2937] bg-[#0A0F1E] shrink-0">
      {/* Left: hamburger (mobile) */}
      <button
        onClick={onMenuToggle}
        className="lg:hidden p-2 rounded-lg text-[#9CA3AF] hover:text-[#F9FAFB] hover:bg-[#111827] transition-colors"
        aria-label="Open menu"
      >
        <Menu size={18} />
      </button>

      {/* Search bar */}
      <div className="hidden sm:flex items-center gap-2 bg-[#111827] border border-[#1F2937] rounded-lg px-3 py-1.5 w-64">
        <Search size={14} className="text-[#6B7280] shrink-0" />
        <input
          type="text"
          value={searchValue}
          onChange={e => setSearchValue(e.target.value)}
          placeholder="Search health data..."
          className="bg-transparent text-sm text-[#F9FAFB] placeholder-[#6B7280] outline-none w-full"
        />
      </div>

      {/* Right: status pill + notification */}
      <div className="flex items-center gap-3">
        <div className="hidden sm:flex items-center gap-1.5 bg-[#10B981]/10 border border-[#10B981]/20 rounded-full px-3 py-1">
          <span className="w-1.5 h-1.5 rounded-full bg-[#10B981] animate-pulse" />
          <span className="text-[#10B981] text-xs font-medium">AI Ready</span>
        </div>
        <button className="p-2 rounded-lg text-[#9CA3AF] hover:text-[#F9FAFB] hover:bg-[#111827] transition-colors relative">
          <Bell size={16} />
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-[#0EA5E9]" />
        </button>
      </div>
    </header>
  )
}
