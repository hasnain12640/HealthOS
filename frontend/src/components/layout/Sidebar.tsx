import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, FlaskConical, Clock, Apple,
  Droplets, MessageCircle, User, Settings, Activity, LogOut, Heart,
  Watch, CalendarDays, History,
} from 'lucide-react'
import { useAuthStore } from '../../store/authStore'
import { useT } from '../../i18n/useT'

const navItems = [
  { to: '/dashboard',   icon: LayoutDashboard, labelKey: 'nav.dashboard' as const },
  { to: '/lab-reports', icon: FlaskConical,    labelKey: 'nav.lab_reports' as const },
  { to: '/history',     icon: History,         labelKey: 'nav.history' as const },
  { to: '/timeline',    icon: Clock,           labelKey: 'nav.timeline' as const },
  { to: '/nutrition',   icon: Apple,           labelKey: 'nav.nutrition' as const },
  { to: '/hydration',   icon: Droplets,        labelKey: 'nav.hydration' as const },
  { to: '/activity',    icon: Activity,        labelKey: 'nav.activity' as const },
  { to: '/wearables',   icon: Watch,           labelKey: 'nav.wearables' as const },
  { to: '/assistant',   icon: MessageCircle,   labelKey: 'nav.ai_assistant' as const },
  { to: '/plan',        icon: CalendarDays,    labelKey: 'nav.seven_day_plan' as const },
]

const bottomItems = [
  { to: '/profile',  icon: User,     labelKey: 'nav.profile' as const },
  { to: '/settings', icon: Settings, labelKey: 'nav.settings' as const },
]

interface SidebarProps {
  onClose?: () => void
}

export function Sidebar({ onClose }: SidebarProps) {
  const { user, logout, profile } = useAuthStore()
  const navigate = useNavigate()
  const t = useT()

  const items = profile?.sex === 'female'
    ? [...navItems, { to: '/womens-health', icon: Heart, labelKey: 'nav.womens_health' as const }]
    : navItems

  const initials = user?.name
    ? user.name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()
    : 'U'

  const handleLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <aside className="flex flex-col h-full bg-bg-base border-r border-border w-60 shrink-0">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-5 py-5 border-b border-border">
        <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
          <span className="text-white font-bold text-sm">H</span>
        </div>
        <div>
          <span className="text-text-primary font-semibold text-sm">HealthOS</span>
          <p className="text-text-muted text-[10px] leading-tight">{t['sidebar.subtitle']}</p>
        </div>
      </div>

      {/* Main nav */}
      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-0.5">
        {items.map(({ to, icon: Icon, labelKey }) => (
          <NavLink
            key={to}
            to={to}
            onClick={onClose}
            className={({ isActive }) =>
              [
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary text-white shadow-[0_0_20px_rgba(14,165,233,0.25)]'
                  : 'text-text-secondary hover:bg-bg-surface hover:text-text-primary',
              ].join(' ')
            }
          >
            <Icon size={16} />
            {t[labelKey]}
          </NavLink>
        ))}
      </nav>

      {/* Bottom nav */}
      <div className="border-t border-border py-3 px-3 space-y-0.5">
        {bottomItems.map(({ to, icon: Icon, labelKey }) => (
          <NavLink
            key={to}
            to={to}
            onClick={onClose}
            className={({ isActive }) =>
              [
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary text-white shadow-[0_0_20px_rgba(14,165,233,0.25)]'
                  : 'text-text-secondary hover:bg-bg-surface hover:text-text-primary',
              ].join(' ')
            }
          >
            <Icon size={16} />
            {t[labelKey]}
          </NavLink>
        ))}

        {/* User chip + logout */}
        <div className="px-3 py-2.5 mt-1 space-y-2">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center shrink-0">
              <span className="text-primary text-xs font-semibold">{initials}</span>
            </div>
            <div className="min-w-0">
              <p className="text-text-primary text-xs font-medium truncate">{user?.name ?? 'User'}</p>
              <p className="text-text-muted text-[10px] truncate">{user?.email ?? ''}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium text-text-secondary hover:bg-bg-elevated hover:text-text-primary transition-colors"
          >
            <LogOut size={14} /> {t['sidebar.logout']}
          </button>
        </div>
      </div>
    </aside>
  )
}
