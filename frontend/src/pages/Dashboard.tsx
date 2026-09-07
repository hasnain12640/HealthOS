import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Activity, AlertTriangle, Apple, BedDouble, Bot, CalendarDays, ChevronRight, CirclePlus, Clock3,
  Droplets, Flame, FlaskConical, Footprints, Heart, HeartPulse, Moon, Upload, Watch,
} from 'lucide-react'
import { Badge, PageWrapper, Spinner } from '../components/ui'
import { AnatomyExplorer } from '../components/dashboard/AnatomyExplorer'
import { DashboardInsight } from '../components/dashboard/DashboardInsight'
import { getDashboard, type DashboardData } from '../services/dashboardService'
import { logHydration } from '../services/lifestyleService'
import { getInsight, type InsightData } from '../services/planService'
import { useT } from '../i18n/useT'
import { onVoiceRefresh } from '../utils/voiceEvents'

type IconType = typeof Activity

const timelineIcons: Record<string, IconType> = {
  lab: FlaskConical,
  nutrition: Apple,
  hydration: Droplets,
  ai_insight: Bot,
  plan: CalendarDays,
  activity: Activity,
  wearable: Watch,
  cycle: Heart,
  cycle_symptom: HeartPulse,
}

const timelineColors: Record<string, string> = {
  lab: 'text-primary border-primary/25 bg-primary/10',
  nutrition: 'text-accent border-accent/25 bg-accent/10',
  hydration: 'text-primary-light border-primary-light/25 bg-primary-light/10',
  ai_insight: 'text-primary-light border-primary-light/25 bg-primary-light/10',
  plan: 'text-warning border-warning/25 bg-warning/10',
  activity: 'text-accent border-accent/25 bg-accent/10',
  wearable: 'text-primary border-primary/25 bg-primary/10',
  cycle: 'text-status-high border-status-high/25 bg-status-high/10',
  cycle_symptom: 'text-status-low border-status-low/25 bg-status-low/10',
}

function formatLiters(milliliters: number) {
  return `${(milliliters / 1000).toFixed(1)} L`
}

function formatSyncTime(value: string) {
  const date = new Date(value)
  return Number.isNaN(date.getTime())
    ? value
    : new Intl.DateTimeFormat(undefined, { hour: 'numeric', minute: '2-digit', month: 'short', day: 'numeric' }).format(date)
}

function formatEventDate(value: string) {
  const date = new Date(value)
  return Number.isNaN(date.getTime())
    ? value
    : new Intl.DateTimeFormat(undefined, { hour: 'numeric', minute: '2-digit' }).format(date)
}

function CircularPercent({ percent, tone = 'primary' }: { percent: number; tone?: 'primary' | 'accent' }) {
  const size = 44
  const stroke = 4
  const radius = (size - stroke) / 2
  const circumference = radius * 2 * Math.PI
  const offset = circumference - (Math.min(percent, 100) / 100) * circumference
  const colorClass = tone === 'accent' ? 'text-accent' : 'text-primary'

  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg className="-rotate-90" width={size} height={size}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={stroke}
          fill="transparent"
          className="text-bg-elevated"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={stroke}
          fill="transparent"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className={`${colorClass} transition-all duration-500`}
        />
      </svg>
      <span className="absolute text-[10px] font-semibold text-text-primary">{Math.round(percent)}%</span>
    </div>
  )
}

function DashboardStat({
  icon: Icon,
  label,
  value,
  detail,
  tone = 'primary',
  badge,
  circularPercent,
}: {
  icon: IconType
  label: string
  value: string
  detail: string
  tone?: 'primary' | 'violet' | 'cyan' | 'green'
  badge?: { label: string; variant: 'high' | 'low' | 'normal' }
  circularPercent?: number
}) {
  const toneClass = {
    primary: 'border-primary/25 bg-primary/10 text-primary',
    violet: 'border-primary-light/25 bg-primary-light/10 text-primary-light',
    cyan: 'border-primary-light/25 bg-primary-light/10 text-primary-light',
    green: 'border-accent/25 bg-accent/10 text-accent',
  }[tone]

  return (
    <div className="dashboard-glass dashboard-hover rounded-2xl border border-border p-4">
      <div className="flex items-start justify-between gap-3">
        <span className={`flex h-9 w-9 items-center justify-center rounded-xl border ${toneClass}`}><Icon size={16} /></span>
        <div className="flex flex-col items-end gap-1.5">
          <span className="text-[10px] uppercase tracking-[0.14em] text-text-muted">{label}</span>
          {badge && <Badge label={badge.label} variant={badge.variant} size="sm" />}
        </div>
      </div>
      <div className="mt-3 flex items-end justify-between gap-3">
        <div className="min-w-0">
          <p className="text-2xl font-semibold tracking-tight text-text-primary">{value}</p>
          <p className="mt-0.5 text-xs text-text-secondary">{detail}</p>
        </div>
        {circularPercent != null && <CircularPercent percent={circularPercent} tone={tone === 'cyan' ? 'primary' : 'accent'} />}
      </div>
    </div>
  )
}

function PriorityCard({ priority }: { priority: DashboardData['priorities'][0] }) {
  const t = useT()
  const badgeLabel = priority.severity === 'high' ? t['insight.urgency_high'] : priority.severity === 'medium' ? t['insight.urgency_medium'] : t['insight.urgency_low']

  return (
    <div className="rounded-2xl border border-border bg-bg-base/40 p-3.5">
      <div className="flex items-start justify-between gap-3">
        <p className="text-xs font-semibold leading-relaxed text-text-primary">{priority.title}</p>
        <Badge
          label={badgeLabel}
          variant={priority.severity === 'high' ? 'high' : priority.severity === 'medium' ? 'low' : 'normal'}
          size="sm"
        />
      </div>
      <p className="mt-2 text-xs leading-relaxed text-text-secondary">{priority.observed_data}</p>
      <p className="mt-2 rounded-lg border border-accent/15 bg-accent/5 px-2.5 py-2 text-xs leading-relaxed text-text-secondary">{priority.suggested_action}</p>
    </div>
  )
}

function MetricCell({ icon: Icon, label, value }: { icon: IconType; label: string; value: string }) {
  return (
    <div className="rounded-xl bg-bg-base/45 p-2.5">
      <div className="flex items-center gap-1.5 text-text-muted"><Icon size={12} className="text-primary" /><span className="truncate text-[10px]">{label}</span></div>
      <p className="mt-1 truncate text-sm font-semibold text-text-primary" title={value}>{value}</p>
    </div>
  )
}

function LatestLabsCard({ labSummary }: { labSummary: DashboardData['lab_summary'] }) {
  const t = useT()
  const navigate = useNavigate()

  return (
    <section className="dashboard-glass overflow-hidden rounded-3xl border border-border">
      <div className="flex items-center justify-between gap-3 border-b border-border px-5 py-4">
        <div className="flex items-center gap-2"><FlaskConical size={15} className="text-primary" /><h2 className="text-sm font-semibold text-text-primary">{t['dashboard.latest_labs']}</h2></div>
        <button type="button" onClick={() => navigate('/lab-reports')} className="inline-flex items-center gap-1 text-xs text-primary hover:underline">{t['dashboard.view_all']}<ChevronRight size={13} /></button>
      </div>
      {labSummary.report_id ? (
        <div className="grid grid-cols-2 gap-px bg-border sm:grid-cols-3">
          {labSummary.biomarkers.slice(0, 6).map(biomarker => (
            <div key={biomarker.id} className="min-w-0 bg-bg-surface p-4">
              <p className="truncate text-[11px] text-text-muted" title={biomarker.name}>{biomarker.name}</p>
              <p className="mt-1 text-sm font-semibold text-text-primary">{biomarker.value} <span className="text-[10px] font-normal text-text-muted">{biomarker.unit}</span></p>
              <div className="mt-2 flex flex-wrap items-center gap-1.5">
                <Badge label={biomarker.status} variant={biomarker.status} size="sm" />
                {(biomarker.reference_low != null || biomarker.reference_high != null) && <span className="text-[10px] text-text-muted">{biomarker.reference_low ?? '—'}–{biomarker.reference_high ?? '—'}</span>}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center p-6 text-center">
          <FlaskConical size={24} className="text-text-muted" />
          <p className="mt-3 text-xs font-medium text-text-primary">{t['dashboard.no_lab_data']}</p>
          <p className="mt-1 max-w-xs text-xs leading-relaxed text-text-secondary">{t['dashboard.no_lab_reports_desc']}</p>
          <div className="mt-4 flex w-full max-w-xs flex-col gap-2">
            <button type="button" onClick={() => navigate('/lab-reports')} className="inline-flex items-center justify-center gap-2 rounded-lg bg-primary px-3 py-2 text-xs font-semibold text-white transition-colors hover:bg-primary-dark"><Upload size={14} />{t['dashboard.upload_report']}</button>
            <button type="button" onClick={() => navigate('/lab-reports')} className="inline-flex items-center justify-center gap-2 rounded-lg border border-border-subtle bg-bg-base/50 px-3 py-2 text-xs font-medium text-text-primary transition-colors hover:border-primary/40 hover:text-primary">{t['dashboard.add_manually']}</button>
          </div>
        </div>
      )}
    </section>
  )
}

function NutritionCard({ nutrition }: { nutrition: DashboardData['nutrition'] }) {
  const t = useT()

  return (
    <section className="dashboard-glass overflow-hidden rounded-3xl border border-border p-5">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2"><Apple size={15} className="text-accent" /><h2 className="text-sm font-semibold text-text-primary">{t['nav.nutrition']}</h2></div>
        <span className="inline-flex items-center gap-1 rounded-full border border-border-subtle bg-bg-base/50 px-2 py-0.5 text-[10px] text-text-secondary"><CalendarDays size={10} />{t['dashboard.today']}</span>
      </div>
      <div className="mt-4 flex flex-col items-center">
        <div className="relative flex h-24 w-24 items-center justify-center rounded-full border-4 border-bg-elevated">
          <span className="text-xl font-semibold text-text-primary">{nutrition.total_calories}</span>
          <span className="absolute -bottom-1 text-[9px] text-text-muted">{t['dashboard.daily_goal']}</span>
        </div>
      </div>
      <div className="mt-4 grid grid-cols-3 gap-2">
        <MacroCell label={t['dashboard.protein']} value={`${nutrition.total_protein_g}g`} color="bg-status-normal" />
        <MacroCell label={t['dashboard.carbs']} value={`${nutrition.total_carbs_g}g`} color="bg-primary-light" />
        <MacroCell label={t['dashboard.fat']} value={`${nutrition.total_fat_g}g`} color="bg-warning" />
      </div>
    </section>
  )
}

function MacroCell({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="flex flex-col items-center gap-1 rounded-xl bg-bg-base/45 py-2">
      <div className="flex items-center gap-1"><span className={`h-1.5 w-1.5 rounded-full ${color}`} /><span className="text-[10px] text-text-secondary">{label}</span></div>
      <span className="text-sm font-semibold text-text-primary">{value}</span>
    </div>
  )
}

function ActivityCard({ activitySteps, wearable }: { activitySteps: number; wearable: DashboardData['wearable'] }) {
  const t = useT()

  return (
    <section className="dashboard-glass overflow-hidden rounded-3xl border border-border p-5">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2"><Activity size={15} className="text-accent" /><h2 className="text-sm font-semibold text-text-primary">{t['nav.activity']}</h2></div>
        <span className="inline-flex items-center gap-1 rounded-full border border-border-subtle bg-bg-base/50 px-2 py-0.5 text-[10px] text-text-secondary"><CalendarDays size={10} />{t['dashboard.today']}</span>
      </div>
      {activitySteps > 0 ? (
        <div className="mt-4">
          <p className="text-2xl font-semibold text-text-primary">{activitySteps.toLocaleString()}</p>
          <p className="text-xs text-text-secondary">{t['wearables.metric_steps']}</p>
          {wearable?.active_calories != null && (
            <div className="mt-3 flex items-center gap-2 rounded-xl bg-bg-base/45 px-3 py-2">
              <Flame size={14} className="text-warning" />
              <span className="text-xs text-text-secondary">{wearable.active_calories} {t['wearables.metric_active_calories']}</span>
            </div>
          )}
        </div>
      ) : (
        <div className="mt-4 flex flex-col items-center rounded-2xl border border-dashed border-border-subtle bg-bg-base/45 p-4 text-center">
          <Activity size={24} className="text-text-muted" />
          <p className="mt-2 text-xs font-medium text-text-primary">{t['dashboard.no_activity_data']}</p>
          <p className="mt-1 text-xs leading-relaxed text-text-secondary">{t['dashboard.start_moving']}</p>
        </div>
      )}
    </section>
  )
}

function SleepCard({ sleep }: { sleep: DashboardData['sleep'] }) {
  const t = useT()

  return (
    <section className="dashboard-glass overflow-hidden rounded-3xl border border-border p-5">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2"><Moon size={15} className="text-primary-light" /><h2 className="text-sm font-semibold text-text-primary">{t['dashboard.sleep']}</h2></div>
        <span className="inline-flex items-center gap-1 rounded-full border border-border-subtle bg-bg-base/50 px-2 py-0.5 text-[10px] text-text-secondary"><CalendarDays size={10} />{t['dashboard.today']}</span>
      </div>
      <div className="mt-4 flex flex-col items-center">
        <div className="relative flex h-24 w-24 items-center justify-center rounded-full border-4 border-bg-elevated">
          <BedDouble size={20} className="absolute top-5 text-text-muted" />
          <span className="mt-4 text-xl font-semibold text-text-primary">{sleep.avg_hours}h</span>
        </div>
        <p className="mt-2 text-xs text-text-secondary">{t['common.of']} {sleep.target_hours}h {t['dashboard.target'].toLowerCase()}</p>
      </div>
    </section>
  )
}

export function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [insightData, setInsightData] = useState<InsightData | null>(null)
  const [showHydrationForm, setShowHydrationForm] = useState(false)
  const [hydrationAmount, setHydrationAmount] = useState('250')
  const [hydrationError, setHydrationError] = useState<string | null>(null)
  const [savingHydration, setSavingHydration] = useState(false)
  const hasLoaded = useRef(false)
  const navigate = useNavigate()
  const t = useT()

  const loadDashboard = useCallback(async () => {
    if (hasLoaded.current) setRefreshing(true)
    else setLoading(true)
    setError(null)

    try {
      const dashboard = await getDashboard()
      setData(dashboard)
      try {
        const insight = await getInsight()
        setInsightData(insight)
        setData(await getDashboard())
      } catch {
        setInsightData(null)
      }
    } catch {
      setError(t['common.backend_not_reachable'])
    } finally {
      hasLoaded.current = true
      setLoading(false)
      setRefreshing(false)
    }
  }, [t])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadDashboard()
    }, 0)
    return () => window.clearTimeout(timer)
  }, [loadDashboard])

  useEffect(() => onVoiceRefresh((scopes) => {
    if (scopes.includes('dashboard')) void loadDashboard()
  }), [loadDashboard])

  const handleHydrationSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const amount = Number(hydrationAmount)
    if (!Number.isFinite(amount) || amount <= 0) {
      setHydrationError(t['dashboard.hydration_amount_error'])
      return
    }

    setSavingHydration(true)
    setHydrationError(null)
    try {
      await logHydration(Math.round(amount))
      setShowHydrationForm(false)
      await loadDashboard()
    } catch {
      setHydrationError(t['common.backend_not_reachable'])
    } finally {
      setSavingHydration(false)
    }
  }

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Spinner size="lg" label={t['common.loading_health_data']} />
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-3">
        <div className="flex h-12 w-12 items-center justify-center rounded-full border border-danger/20 bg-danger/10"><AlertTriangle size={20} className="text-danger" /></div>
        <p className="text-sm font-medium text-text-primary">{t['common.backend_not_reachable']}</p>
        <p className="max-w-sm text-center text-xs text-text-secondary">{error}</p>
        <button type="button" onClick={() => void loadDashboard()} className="text-xs text-primary underline hover:no-underline">{t['common.retry']}</button>
      </div>
    )
  }

  const { profile, lab_summary, hydration, nutrition, sleep, activity, priorities, timeline, wearable, womens_health, ai_insight } = data
  const firstName = profile.user_name.split(' ')[0]
  const hour = new Date().getHours()
  const greeting = hour >= 5 && hour < 12 ? t['dashboard.good_morning'] : hour < 18 ? t['dashboard.good_afternoon'] : t['dashboard.good_evening']
  const activitySteps = wearable?.steps ?? activity.recent.reduce((total, entry) => total + entry.steps, 0)
  const activityDetail = wearable?.steps != null
    ? wearable.device_name
    : activitySteps > 0 ? t['dashboard.recent_activity'] : t['dashboard.no_activity_data']
  const hydrationPercent = Math.min(hydration.percent, 100)
  const hydrationColor = hydration.percent >= 80 ? 'bg-accent' : hydration.percent >= 50 ? 'bg-warning' : 'bg-primary'
  const isFemaleProfile = profile.sex === 'female'
  const visibleTimeline = isFemaleProfile
    ? timeline
    : timeline.filter(event => event.event_type !== 'cycle' && event.event_type !== 'cycle_symptom')

  const contextPills = (
    <div className="flex max-w-md flex-wrap justify-end gap-2">
      <span className="dashboard-context-pill"><CalendarDays size={12} />{t['dashboard.today']}</span>
      {wearable ? (
        <span className="dashboard-context-pill"><Watch size={12} />{t['dashboard.last_synced']} {formatSyncTime(wearable.last_synced_at)}</span>
      ) : (
        <span className="dashboard-context-pill"><Watch size={12} />{t['wearables.no_device']}</span>
      )}
      {refreshing && <span className="dashboard-context-pill text-primary"><Clock3 size={12} />{t['dashboard.refreshing']}</span>}
    </div>
  )

  const topPriority = priorities[0]

  return (
    <PageWrapper title={`${greeting}, ${firstName}`} subtitle={t['dashboard.your_health_journey']} action={contextPills}>
      <div className="dashboard-page space-y-5 pb-4">
        {/* Summary cards */}
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <DashboardStat
            icon={AlertTriangle}
            label={t['dashboard.health_priorities']}
            value={String(priorities.length)}
            detail={t['dashboard.needs_attention']}
            tone="primary"
            badge={topPriority ? { label: topPriority.severity === 'high' ? t['insight.urgency_high'] : topPriority.severity === 'medium' ? t['insight.urgency_medium'] : t['insight.urgency_low'], variant: topPriority.severity === 'high' ? 'high' : topPriority.severity === 'medium' ? 'low' : 'normal' } : undefined}
          />
          <DashboardStat icon={Moon} label={t['dashboard.avg_sleep']} value={`${sleep.avg_hours}h`} detail={`${t['dashboard.target']} ${sleep.target_hours}h`} tone="violet" />
          <DashboardStat icon={Droplets} label={t['dashboard.hydration_today']} value={formatLiters(hydration.today_ml)} detail={`${t['common.of']} ${formatLiters(hydration.target_ml)}`} tone="cyan" circularPercent={hydrationPercent} />
          <DashboardStat icon={Activity} label={t['dashboard.activity']} value={activitySteps > 0 ? activitySteps.toLocaleString() : '—'} detail={activityDetail} tone="green" />
        </div>

        {/* Three-column main area */}
        <div className="grid gap-5 lg:grid-cols-[minmax(16rem,0.9fr)_minmax(0,1.5fr)_minmax(16rem,1fr)] lg:items-start">
          {/* Health Priorities */}
          <aside className="dashboard-glass space-y-4 rounded-3xl border border-border p-4 sm:p-5">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="dashboard-eyebrow">{t['dashboard.priority_signal']}</p>
                <h2 className="mt-1 text-base font-semibold text-text-primary">{t['dashboard.health_priorities']}</h2>
              </div>
              <span className="flex h-8 min-w-8 items-center justify-center rounded-full border border-warning/20 bg-warning/10 px-2 text-xs font-semibold text-warning">{priorities.length}</span>
            </div>
            {priorities.length > 0 ? (
              <div className="space-y-2.5">{priorities.map(priority => <PriorityCard key={priority.id} priority={priority} />)}</div>
            ) : (
              <p className="rounded-xl bg-bg-base/45 p-3 text-xs leading-relaxed text-text-secondary">{t['dashboard.no_priorities']}</p>
            )}
          </aside>

          {/* Anatomy hero */}
          <AnatomyExplorer data={data} />

          {/* Right column */}
          <aside className="space-y-5">
            <section className="dashboard-glass rounded-3xl border border-border p-4 sm:p-5">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2"><Watch size={15} className="text-primary" /><h2 className="text-sm font-semibold text-text-primary">{t['dashboard.recovery_activity']}</h2></div>
                <button type="button" onClick={() => navigate('/wearables')} className="inline-flex items-center gap-1 text-xs text-primary hover:underline">{wearable ? t['dashboard.view_all'] : t['dashboard.connect_device']}<ChevronRight size={13} /></button>
              </div>
              {wearable ? (
                <>
                  <p className="mt-1 text-xs text-text-muted">{wearable.device_name} · {t['dashboard.last_synced']} {formatSyncTime(wearable.last_synced_at)}</p>
                  <div className="mt-4 grid grid-cols-2 gap-2">
                    {wearable.steps != null && <MetricCell icon={Footprints} label={t['wearables.metric_steps']} value={wearable.steps.toLocaleString()} />}
                    {wearable.active_calories != null && <MetricCell icon={Flame} label={t['wearables.metric_active_calories']} value={`${wearable.active_calories} kcal`} />}
                    {wearable.resting_heart_rate != null && <MetricCell icon={HeartPulse} label={t['wearables.metric_resting_heart_rate']} value={`${wearable.resting_heart_rate} bpm`} />}
                    {wearable.sleep_hours != null && <MetricCell icon={Moon} label={t['wearables.metric_sleep']} value={`${wearable.sleep_hours}h`} />}
                  </div>
                </>
              ) : (
                <div className="mt-4 rounded-2xl border border-dashed border-border-subtle bg-bg-base/45 p-4 text-center">
                  <Watch size={19} className="mx-auto text-text-muted" />
                  <p className="mt-2 text-xs font-medium text-text-primary">{t['wearables.no_device']}</p>
                  <p className="mt-1 text-xs leading-relaxed text-text-secondary">{t['dashboard.wearable_empty']}</p>
                </div>
              )}
            </section>

            <section className="dashboard-glass rounded-3xl border border-border p-4 sm:p-5">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2"><Droplets size={15} className="text-primary-light" /><h2 className="text-sm font-semibold text-text-primary">{t['dashboard.hydration_today']}</h2></div>
                <span className="text-xs font-semibold text-primary-light">{hydration.percent}%</span>
              </div>
              <p className="mt-3 text-2xl font-semibold text-text-primary">{formatLiters(hydration.today_ml)}</p>
              <p className="text-xs text-text-secondary">{t['common.of']} {formatLiters(hydration.target_ml)} {t['dashboard.target'].toLowerCase()}</p>
              <div className="mt-4 h-2 overflow-hidden rounded-full bg-bg-elevated"><div className={`dashboard-progress h-full rounded-full ${hydrationColor}`} style={{ width: `${hydrationPercent}%` }} /></div>
              <div className="mt-4 flex items-center justify-between gap-3">
                <span className="text-[11px] text-text-muted">{hydration.target_ml > hydration.today_ml ? t['dashboard.ml_remaining'].replace('{{ml}}', String(hydration.target_ml - hydration.today_ml)) : t['dashboard.target_reached']}</span>
                <button type="button" onClick={() => { setShowHydrationForm(open => !open); setHydrationError(null) }} className="inline-flex shrink-0 items-center gap-1.5 rounded-lg border border-primary/30 bg-primary/10 px-2.5 py-1.5 text-xs font-medium text-primary transition-colors hover:bg-primary/20"><CirclePlus size={13} />{t['dashboard.add_water']}</button>
              </div>
              {showHydrationForm && (
                <form onSubmit={handleHydrationSubmit} className="mt-3 rounded-xl border border-primary/20 bg-bg-base/60 p-3">
                  <label htmlFor="dashboard-water-amount" className="text-[11px] font-medium text-text-secondary">{t['dashboard.water_amount']}</label>
                  <div className="mt-1.5 flex gap-2">
                    <input id="dashboard-water-amount" type="number" min="1" step="1" value={hydrationAmount} onChange={event => setHydrationAmount(event.target.value)} className="min-w-0 flex-1 rounded-lg border border-border-subtle bg-bg-surface px-2.5 py-1.5 text-sm text-text-primary outline-none focus:border-primary" />
                    <button type="submit" disabled={savingHydration} className="rounded-lg bg-primary px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-primary-dark disabled:cursor-not-allowed disabled:opacity-60">{savingHydration ? t['common.loading'] : t['common.save']}</button>
                  </div>
                  {hydrationError && <p className="mt-1.5 text-[11px] text-danger">{hydrationError}</p>}
                </form>
              )}
            </section>

            {isFemaleProfile && womens_health && (
              <section className="dashboard-glass rounded-3xl border border-cycle/25 p-4 sm:p-5">
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2"><Heart size={15} className="text-cycle-light" /><h2 className="text-sm font-semibold text-text-primary">{t['womens.dashboard_card']}</h2></div>
                  <button type="button" onClick={() => navigate('/womens-health')} className="inline-flex items-center gap-1 text-xs text-cycle-light hover:underline">{t['dashboard.view_all']}<ChevronRight size={13} /></button>
                </div>
                <div className="mt-4 grid grid-cols-2 gap-2">
                  <MetricCell icon={CalendarDays} label={t['womens.current_cycle']} value={womens_health.current_cycle_day != null ? t['womens.day_of'].replace('{{day}}', String(womens_health.current_cycle_day)).replace('{{total}}', String(womens_health.average_cycle_length ?? 28)) : '—'} />
                  <MetricCell icon={Heart} label={t['womens.phase']} value={womens_health.current_phase ? t[`womens.phase_${womens_health.current_phase}` as keyof typeof t] : '—'} />
                </div>
                <p className="mt-3 text-xs text-text-secondary">{t['womens.next_period']}: {womens_health.predicted_period_start ? new Date(`${womens_health.predicted_period_start}T00:00:00`).toLocaleDateString(undefined, { day: 'numeric', month: 'short' }) : '—'}</p>
                {womens_health.needs_more_data && <p className="mt-2 text-xs text-warning">{t['womens.needs_more_data']}</p>}
              </section>
            )}
          </aside>
        </div>

        {/* Four lower cards */}
        <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
          <LatestLabsCard labSummary={lab_summary} />
          <NutritionCard nutrition={nutrition} />
          <ActivityCard activitySteps={activitySteps} wearable={wearable} />
          <SleepCard sleep={sleep} />
        </div>

        {/* AI Health Intelligence */}
        <DashboardInsight insightData={insightData} fallbackInsight={ai_insight} onAskAI={() => navigate('/assistant')} userSex={profile.sex as 'male' | 'female'} />

        {/* Recent Activity */}
        <section className="dashboard-glass rounded-3xl border border-border p-5">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <Clock3 size={15} className="text-primary" />
              <div>
                <h2 className="text-sm font-semibold text-text-primary">{t['dashboard.recent_activity_title']}</h2>
                <p className="text-xs text-text-secondary">{t['dashboard.recent_activity_subtitle']}</p>
              </div>
            </div>
            <button type="button" onClick={() => navigate('/timeline')} className="inline-flex items-center gap-1 text-xs text-primary hover:underline">{t['dashboard.view_all']}<ChevronRight size={13} /></button>
          </div>
          {visibleTimeline.length > 0 ? (
            <div className="mt-4 space-y-2">
              {visibleTimeline.slice(0, 5).map(event => {
                const Icon = timelineIcons[event.event_type] ?? Activity
                const color = timelineColors[event.event_type] ?? timelineColors.activity
                return (
                  <div key={event.id} className="flex items-center gap-3 rounded-xl border border-border bg-bg-base/45 px-3 py-2.5">
                    <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full border ${color}`}><Icon size={14} /></span>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-start justify-between gap-3">
                        <p className="text-xs font-medium text-text-primary">{event.title}</p>
                        <span className="shrink-0 text-[10px] text-text-muted">{formatEventDate(event.date)}</span>
                      </div>
                      <p className="mt-0.5 truncate text-xs text-text-secondary">{event.description}</p>
                    </div>
                    <ChevronRight size={14} className="shrink-0 text-text-muted" />
                  </div>
                )
              })}
            </div>
          ) : (
            <p className="mt-4 rounded-xl bg-bg-base/45 p-4 text-center text-xs text-text-secondary">{t['dashboard.no_timeline_events']}</p>
          )}
        </section>
      </div>
    </PageWrapper>
  )
}
