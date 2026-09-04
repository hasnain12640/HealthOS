import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, FlaskConical, Clock, Apple,
  Droplets, MessageCircle, CalendarDays, User, Settings, Activity, LogOut,
} from 'lucide-react'
import { useAuthStore } from '../../store/authStore'

const navItems = [
  { to: '/dashboard',  icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/lab-reports', icon: FlaskConical,   label: 'Lab Reports' },
  { to: '/timeline',   icon: Clock,           label: 'Timeline' },
  { to: '/nutrition',  icon: Apple,           label: 'Nutrition' },
  { to: '/hydration',  icon: Droplets,        label: 'Hydration' },
  { to: '/activity',   icon: Activity,        label: 'Activity' },
  { to: '/assistant',  icon: MessageCircle,   label: 'AI Assistant' },
  { to: '/plan',       icon: CalendarDays,    label: '7-Day Plan' },
]

const bottomItems = [
  { to: '/profile',  icon: User,     label: 'Profile' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

interface SidebarProps {
  onClose?: () => void
}

export function Sidebar({ onClose }: SidebarProps) {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const initials = user?.name
    ? user.name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()
    : 'U'

  const handleLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <aside className="flex flex-col h-full bg-[#0A0F1E] border-r border-[#1F2937] w-60 shrink-0">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-5 py-5 border-b border-[#1F2937]">
        <div className="w-8 h-8 rounded-lg bg-[#0EA5E9] flex items-center justify-center">
          <span className="text-white font-bold text-sm">H</span>
        </div>
        <div>
          <span className="text-[#F9FAFB] font-semibold text-sm">HealthOS</span>
          <p className="text-[#6B7280] text-[10px] leading-tight">Health Intelligence</p>
        </div>
      </div>

      {/* Main nav */}
      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-0.5">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            onClick={onClose}
            className={({ isActive }) =>
              [
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-[#0EA5E9]/10 text-[#0EA5E9]'
                  : 'text-[#9CA3AF] hover:bg-[#111827] hover:text-[#F9FAFB]',
              ].join(' ')
            }
          >
            <Icon size={16} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Bottom nav */}
      <div className="border-t border-[#1F2937] py-3 px-3 space-y-0.5">
        {bottomItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            onClick={onClose}
            className={({ isActive }) =>
              [
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-[#0EA5E9]/10 text-[#0EA5E9]'
                  : 'text-[#9CA3AF] hover:bg-[#111827] hover:text-[#F9FAFB]',
              ].join(' ')
            }
          >
            <Icon size={16} />
            {label}
          </NavLink>
        ))}

        {/* User chip + logout */}
        <div className="px-3 py-2.5 mt-1 space-y-2">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-full bg-[#0EA5E9]/20 flex items-center justify-center shrink-0">
              <span className="text-[#0EA5E9] text-xs font-semibold">{initials}</span>
            </div>
            <div className="min-w-0">
              <p className="text-[#F9FAFB] text-xs font-medium truncate">{user?.name ?? 'User'}</p>
              <p className="text-[#6B7280] text-[10px] truncate">{user?.email ?? ''}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium text-[#9CA3AF] hover:bg-[#1F2937] hover:text-[#F9FAFB] transition-colors"
          >
            <LogOut size={14} /> Log out
          </button>
        </div>
      </div>
    </aside>
  )
}
