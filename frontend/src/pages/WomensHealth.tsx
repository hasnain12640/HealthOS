import { useEffect, useState, useCallback } from 'react'
import { PageWrapper, Card, Badge, Button, Spinner } from '../components/ui'
import { useT } from '../i18n/useT'
import { useSettingsStore } from '../store/settingsStore'
import { useAuthStore } from '../store/authStore'
import {
  getCurrentCycle, getCycleCalendar, listSymptoms, listCycles,
  createCycle, createSymptom, deleteSymptom,
  type CurrentCycleData, type CycleCalendar, type CycleSymptomData, type CycleData,
  type SymptomType, type Severity, type CyclePhase,
} from '../services/cycleService'
import {
  Heart, CalendarDays, ChevronLeft, ChevronRight, Droplets, Sprout, Sun, Moon,
  AlertTriangle, Plus, Trash2, Info, CalendarCheck,
} from 'lucide-react'
import { VoiceAgentTrigger } from '../components/voice/VoiceAgentTrigger'
import { onVoiceRefresh } from '../utils/voiceEvents'

const SYMPTOM_TYPES: SymptomType[] = [
  'cramps', 'headache', 'bloating', 'fatigue', 'mood_changes',
  'breast_tenderness', 'acne', 'appetite_change', 'nausea', 'back_pain', 'other',
]

const SEVERITIES: Severity[] = ['mild', 'moderate', 'severe']

const phaseConfig: Record<CyclePhase, { variant: 'normal' | 'low' | 'high' | 'critical' | 'info' | 'default'; icon: React.ElementType }> = {
  menstrual: { variant: 'critical', icon: Droplets },
  follicular: { variant: 'normal', icon: Sprout },
  ovulatory: { variant: 'info', icon: Sun },
  luteal: { variant: 'default', icon: Moon },
}

const severityBadgeVariant: Record<Severity, 'normal' | 'high' | 'critical'> = {
  mild: 'normal',
  moderate: 'high',
  severe: 'critical',
}

function todayIso(): string {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function daysBetween(fromIso: string, toIso: string): number {
  const from = new Date(fromIso + 'T00:00:00').getTime()
  const to = new Date(toIso + 'T00:00:00').getTime()
  return Math.round((to - from) / 86400000)
}

// 2023-01-01 was a Sunday
const WEEKDAYS = Array.from({ length: 7 }, (_, i) => new Date(2023, 0, 1 + i))

export function WomensHealth() {
  const t = useT()
  const language = useSettingsStore(s => s.language)
  const profile = useAuthStore(s => s.profile)
  const locale = language === 'ur' ? 'ur-PK' : undefined

  const [current, setCurrent] = useState<CurrentCycleData | null>(null)
  const [calendar, setCalendar] = useState<CycleCalendar | null>(null)
  const [calMonth, setCalMonth] = useState(() => {
    const d = new Date()
    return { year: d.getFullYear(), month: d.getMonth() + 1 }
  })
  const [calendarLoading, setCalendarLoading] = useState(false)
  const [symptoms, setSymptoms] = useState<CycleSymptomData[]>([])
  const [cycles, setCycles] = useState<CycleData[]>([])
  const [loading, setLoading] = useState(true)
  const [restricted, setRestricted] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [showPeriodForm, setShowPeriodForm] = useState(false)
  const [showSymptomForm, setShowSymptomForm] = useState(false)
  const [periodStart, setPeriodStart] = useState(todayIso())
  const [periodLength, setPeriodLength] = useState(5)
  const [submittingPeriod, setSubmittingPeriod] = useState(false)
  const [periodError, setPeriodError] = useState<string | null>(null)
  const [selectedSymptom, setSelectedSymptom] = useState<SymptomType | null>(null)
  const [selectedSeverity, setSelectedSeverity] = useState<Severity>('moderate')
  const [submittingSymptom, setSubmittingSymptom] = useState(false)
  const [symptomError, setSymptomError] = useState<string | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const fetchCore = useCallback(async () => {
    const [cur, syms, cyc] = await Promise.all([getCurrentCycle(), listSymptoms(), listCycles()])
    setCurrent(cur)
    setSymptoms(syms)
    setCycles(cyc)
  }, [])

  const fetchCalendar = useCallback(async (year: number, month: number) => {
    setCalendarLoading(true)
    try {
      setCalendar(await getCycleCalendar(year, month))
    } finally {
      setCalendarLoading(false)
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    Promise.all([fetchCore(), fetchCalendar(calMonth.year, calMonth.month)])
      .catch((err: unknown) => {
        if (cancelled) return
        const status = (err as { response?: { status?: number } })?.response?.status
        if (status === 403) setRestricted(true)
        else setError(t['common.backend_not_reachable'])
      })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const refreshAll = useCallback(async () => {
    await Promise.all([fetchCore(), fetchCalendar(calMonth.year, calMonth.month)])
  }, [calMonth.month, calMonth.year, fetchCalendar, fetchCore])

  useEffect(() => onVoiceRefresh((scopes) => {
    if (scopes.includes('womens_health')) {
      void refreshAll().catch(() => setError(t['common.backend_not_reachable']))
    }
  }), [refreshAll, t])

  const changeMonth = (delta: number) => {
    const d = new Date(calMonth.year, calMonth.month - 1 + delta, 1)
    const next = { year: d.getFullYear(), month: d.getMonth() + 1 }
    setCalMonth(next)
    fetchCalendar(next.year, next.month).catch(() => {})
  }

  const backendDetail = (err: unknown): string => {
    const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    return detail ?? t['common.backend_not_reachable']
  }

  const handleLogPeriod = async () => {
    if (!periodStart) return
    setSubmittingPeriod(true)
    setPeriodError(null)
    try {
      await createCycle({ start_date: periodStart, period_length: periodLength || undefined })
      setShowPeriodForm(false)
      await refreshAll()
    } catch (err) {
      setPeriodError(backendDetail(err))
    } finally {
      setSubmittingPeriod(false)
    }
  }

  const handleLogSymptom = async () => {
    if (!selectedSymptom) return
    setSubmittingSymptom(true)
    setSymptomError(null)
    try {
      await createSymptom({ date: todayIso(), symptom_type: selectedSymptom, severity: selectedSeverity })
      setShowSymptomForm(false)
      setSelectedSymptom(null)
      setSelectedSeverity('moderate')
      await refreshAll()
    } catch (err) {
      setSymptomError(backendDetail(err))
    } finally {
      setSubmittingSymptom(false)
    }
  }

  const handleDeleteSymptom = async (id: string) => {
    setDeletingId(id)
    try {
      await deleteSymptom(id)
      await refreshAll()
    } catch {
      setError(t['common.backend_not_reachable'])
    } finally {
      setDeletingId(null)
    }
  }

  const retry = () => {
    setLoading(true)
    setError(null)
    Promise.all([fetchCore(), fetchCalendar(calMonth.year, calMonth.month)])
      .catch(() => setError(t['common.backend_not_reachable']))
      .finally(() => setLoading(false))
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner size="lg" label={t['common.loading_health_data']} />
      </div>
    )
  }

  if (restricted) {
    return (
      <PageWrapper title={t['womens.title']} subtitle={t['womens.subtitle']}>
        <Card>
          <div className="flex flex-col items-center text-center py-8">
            <div className="w-14 h-14 rounded-full bg-danger/10 border border-danger/20 flex items-center justify-center mb-3">
              <AlertTriangle size={24} className="text-danger" />
            </div>
            <p className="text-text-primary font-medium text-sm">{t['womens.restricted']}</p>
          </div>
        </Card>
      </PageWrapper>
    )
  }

  if (error && !current) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3">
        <div className="w-12 h-12 rounded-full bg-danger/10 border border-danger/20 flex items-center justify-center">
          <AlertTriangle size={20} className="text-danger" />
        </div>
        <p className="text-text-primary font-medium text-sm">{t['common.backend_not_reachable']}</p>
        <button onClick={retry} className="text-primary text-xs underline hover:no-underline">
          {t['common.retry']}
        </button>
      </div>
    )
  }

  const fmtDate = (iso: string): string =>
    new Date(iso + 'T00:00:00').toLocaleDateString(locale, { day: 'numeric', month: 'short', year: 'numeric' })

  const prediction = current?.prediction
  const p = prediction ?? null
  const totalDays = p?.current_cycle_length ?? p?.average_cycle_length ?? 28
  const daysUntilNext = p?.predicted_period_start ? daysBetween(todayIso(), p.predicted_period_start) : null
  const phase = p?.current_phase
  const phaseCfg = phase ? phaseConfig[phase] : null
  const PhaseIcon = phaseCfg?.icon

  const monthLabel = new Date(calMonth.year, calMonth.month - 1, 1)
    .toLocaleDateString(locale, { month: 'long', year: 'numeric' })
  const weekdayNames = WEEKDAYS.map(d => d.toLocaleDateString(locale, { weekday: 'short' }))
  const leadingBlanks = new Date(calMonth.year, calMonth.month - 1, 1).getDay()

  const legend = [
    { color: 'bg-[#EC4899]/70', label: t['womens.legend_period'] },
    { color: 'bg-transparent border border-dashed border-[#EC4899]/70', label: t['womens.legend_predicted'] },
    { color: 'bg-[#A78BFA]/50', label: t['womens.legend_fertile'] },
    { color: 'bg-transparent border-2 border-primary/70', label: t['womens.legend_today'] },
    { color: 'bg-accent', label: t['womens.legend_symptom'] },
  ]

  const stats = [
    {
      icon: CalendarDays,
      color: 'text-primary',
      label: t['womens.avg_cycle_length'],
      value: p?.average_cycle_length != null ? String(p.average_cycle_length) : '—',
      unit: p?.average_cycle_length != null ? t['womens.days_unit'] : '',
    },
    {
      icon: Droplets,
      color: 'text-[#EC4899]',
      label: t['womens.avg_period_length'],
      value: p?.average_period_length != null ? String(p.average_period_length) : '—',
      unit: p?.average_period_length != null ? t['womens.days_unit'] : '',
    },
    {
      icon: Heart,
      color: 'text-[#EC4899]',
      label: t['womens.cycles_tracked'],
      value: String(p?.cycles_tracked ?? 0),
      unit: '',
    },
    {
      icon: CalendarCheck,
      color: 'text-accent',
      label: t['womens.next_period_stat'],
      value: p?.predicted_period_start ? fmtDate(p.predicted_period_start) : '—',
      unit: daysUntilNext != null && daysUntilNext >= 0
        ? t['womens.in_days'].replace('{{count}}', String(daysUntilNext))
        : '',
    },
  ]

  return (
    <PageWrapper
      title={t['womens.title']}
      subtitle={t['womens.subtitle']}
      action={profile?.sex === 'female' ? <VoiceAgentTrigger /> : undefined}
    >
      <div className="space-y-6">

        {/* Current Cycle */}
        <Card>
          {p?.has_data ? (
            <>
              <div className="flex flex-col lg:flex-row lg:items-center gap-5">
                <div className="flex items-center gap-4 flex-1">
                  <div className="w-20 h-20 rounded-2xl bg-[#EC4899]/10 border border-[#EC4899]/20 flex flex-col items-center justify-center shrink-0">
                    <span className="text-[#F472B6] text-2xl font-bold leading-none">{p.current_cycle_day}</span>
                    <span className="text-text-muted text-[10px] mt-1">{t['womens.days_unit']}</span>
                  </div>
                  <div>
                    <h3 className="text-text-primary font-semibold text-sm">
                      {t['womens.day_of']
                        .replace('{{day}}', String(p.current_cycle_day))
                        .replace('{{total}}', String(totalDays))}
                    </h3>
                    <div className="flex flex-wrap items-center gap-2 mt-2">
                      {phase && PhaseIcon && (
                        <Badge
                          label={t[`womens.phase_${phase}` as keyof typeof t]}
                          variant={phaseCfg!.variant}
                          size="sm"
                        />
                      )}
                      {p.is_on_period_today && (
                        <Badge label={t['womens.on_period_today']} variant="critical" size="sm" />
                      )}
                    </div>
                    {p.needs_more_data && (
                      <p className="text-warning text-xs mt-2">{t['womens.needs_more_data']}</p>
                    )}
                  </div>
                </div>
                <div className="grid sm:grid-cols-2 gap-3 lg:w-[26rem]">
                  <div className="bg-bg-elevated rounded-lg p-3">
                    <p className="text-text-muted text-[10px] uppercase tracking-wide font-medium mb-1">
                      {t['womens.next_period']}
                    </p>
                    <p className="text-text-primary text-sm font-semibold">
                      {p.predicted_period_start ? fmtDate(p.predicted_period_start) : '—'}
                    </p>
                    {daysUntilNext != null && daysUntilNext >= 0 && (
                      <p className="text-text-muted text-xs mt-0.5">
                        {t['womens.in_days'].replace('{{count}}', String(daysUntilNext))}
                      </p>
                    )}
                  </div>
                  <div className="bg-bg-elevated rounded-lg p-3">
                    <p className="text-text-muted text-[10px] uppercase tracking-wide font-medium mb-1">
                      {t['womens.fertile_window']}
                    </p>
                    <p className="text-text-primary text-sm font-semibold">
                      {p.estimated_fertile_start && p.estimated_fertile_end
                        ? `${fmtDate(p.estimated_fertile_start)} – ${fmtDate(p.estimated_fertile_end)}`
                        : '—'}
                    </p>
                  </div>
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-2 pt-4 mt-4 border-t border-border">
                <Button
                  size="sm"
                  variant={showPeriodForm ? 'secondary' : 'primary'}
                  onClick={() => { setShowPeriodForm(v => !v); setShowSymptomForm(false) }}
                >
                  <Plus size={14} />
                  {t['womens.log_period']}
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => { setShowSymptomForm(v => !v); setShowPeriodForm(false) }}
                >
                  <Plus size={14} />
                  {t['womens.log_symptom']}
                </Button>
              </div>
            </>
          ) : (
            <div className="flex flex-col items-center text-center py-8">
              <div className="w-14 h-14 rounded-full bg-[#EC4899]/10 border border-[#EC4899]/20 flex items-center justify-center mb-3">
                <Heart size={24} className="text-[#F472B6]" />
              </div>
              <h3 className="text-text-primary font-medium text-sm mb-1">{t['womens.no_cycles']}</h3>
              <p className="text-text-secondary text-xs mb-4 max-w-sm">{t['womens.no_cycles_desc']}</p>
              <Button size="sm" onClick={() => setShowPeriodForm(true)}>
                <Plus size={14} />
                {t['womens.log_period']}
              </Button>
            </div>
          )}
        </Card>

        {/* Log Period form */}
        {showPeriodForm && (
          <Card>
            <h3 className="text-text-primary font-semibold text-sm mb-3">{t['womens.log_period']}</h3>
            <div className="grid sm:grid-cols-[1fr_1fr_auto] gap-3 items-end">
              <label className="block">
                <span className="text-text-secondary text-xs block mb-1.5">{t['womens.start_date_label']}</span>
                <input
                  type="date"
                  value={periodStart}
                  max={todayIso()}
                  onChange={e => setPeriodStart(e.target.value)}
                  className="w-full bg-bg-elevated border border-border rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-primary"
                />
              </label>
              <label className="block">
                <span className="text-text-secondary text-xs block mb-1.5">{t['womens.period_length_label']}</span>
                <input
                  type="number"
                  min={1}
                  max={14}
                  value={periodLength}
                  onChange={e => setPeriodLength(Number(e.target.value))}
                  className="w-full bg-bg-elevated border border-border rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-primary"
                />
              </label>
              <div className="flex gap-2">
                <Button size="md" onClick={handleLogPeriod} loading={submittingPeriod} disabled={!periodStart}>
                  {t['womens.submit']}
                </Button>
                <Button size="md" variant="ghost" onClick={() => { setShowPeriodForm(false); setPeriodError(null) }}>
                  {t['common.cancel']}
                </Button>
              </div>
            </div>
            {periodError && <p className="text-danger text-xs mt-2">{periodError}</p>}
          </Card>
        )}

        {/* Log Symptom form */}
        {showSymptomForm && (
          <Card>
            <h3 className="text-text-primary font-semibold text-sm mb-1">{t['womens.log_symptom']}</h3>
            <p className="text-text-secondary text-xs mb-3">{t['womens.select_symptom']}</p>
            <div className="flex flex-wrap gap-2 mb-4">
              {SYMPTOM_TYPES.map(type => (
                <button
                  key={type}
                  type="button"
                  onClick={() => setSelectedSymptom(type)}
                  className={[
                    'px-3 py-1.5 rounded-full text-xs font-medium border transition-colors',
                    selectedSymptom === type
                      ? 'border-[#EC4899]/50 bg-[#EC4899]/15 text-[#F9A8D4]'
                      : 'border-border bg-bg-elevated text-text-secondary hover:text-text-primary',
                  ].join(' ')}
                >
                  {t[`womens.symptom_${type}` as keyof typeof t]}
                </button>
              ))}
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {SEVERITIES.map(sev => (
                <button
                  key={sev}
                  type="button"
                  onClick={() => setSelectedSeverity(sev)}
                  className={[
                    'px-3 py-1.5 rounded-full text-xs font-medium border transition-colors',
                    selectedSeverity === sev
                      ? sev === 'severe'
                        ? 'border-danger/50 bg-danger/15 text-danger'
                        : sev === 'moderate'
                          ? 'border-warning/50 bg-warning/15 text-warning'
                          : 'border-status-normal/50 bg-status-normal/15 text-status-normal'
                      : 'border-border bg-bg-elevated text-text-secondary hover:text-text-primary',
                  ].join(' ')}
                >
                  {t[`womens.severity_${sev}` as keyof typeof t]}
                </button>
              ))}
              <div className="flex gap-2 ml-auto">
                <Button size="sm" onClick={handleLogSymptom} loading={submittingSymptom} disabled={!selectedSymptom}>
                  {t['womens.submit']}
                </Button>
                <Button size="sm" variant="ghost" onClick={() => { setShowSymptomForm(false); setSymptomError(null) }}>
                  {t['common.cancel']}
                </Button>
              </div>
            </div>
            {symptomError && <p className="text-danger text-xs mt-2">{symptomError}</p>}
          </Card>
        )}

        {/* Cycle Calendar */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <CalendarDays size={14} className="text-primary" />
              <h2 className="text-text-primary font-semibold text-sm">{t['womens.calendar']}</h2>
            </div>
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => changeMonth(-1)}
                className="p-1.5 rounded-lg hover:bg-bg-elevated text-text-secondary transition-colors"
                aria-label="Previous month"
              >
                <ChevronLeft size={16} />
              </button>
              <span className="text-text-primary text-xs font-medium min-w-[8rem] text-center">
                {calendarLoading ? '…' : monthLabel}
              </span>
              <button
                type="button"
                onClick={() => changeMonth(1)}
                className="p-1.5 rounded-lg hover:bg-bg-elevated text-text-secondary transition-colors"
                aria-label="Next month"
              >
                <ChevronRight size={16} />
              </button>
            </div>
          </div>

          <div className="grid grid-cols-7 gap-1 mb-1">
            {weekdayNames.map(name => (
              <div key={name} className="text-text-muted text-[10px] font-medium text-center py-1">
                {name}
              </div>
            ))}
          </div>

          <div className={`grid grid-cols-7 gap-1 ${calendarLoading ? 'opacity-50' : ''}`}>
            {Array.from({ length: leadingBlanks }, (_, i) => (
              <div key={`blank-${i}`} />
            ))}
            {calendar?.days.map(day => {
              const classes = day.in_period
                ? 'bg-[#EC4899]/20 text-[#F9A8D4] font-semibold'
                : day.is_predicted_period
                  ? 'border border-dashed border-[#EC4899]/50 text-[#F9A8D4]'
                  : day.is_fertile_window
                    ? 'bg-[#A78BFA]/15 text-[#C4B5FD]'
                    : 'text-text-secondary hover:bg-bg-elevated'
              const todayRing = day.is_today ? 'ring-2 ring-primary/60' : ''
              return (
                <div
                  key={day.date}
                  title={`${day.date}${day.has_symptom ? ` · ${day.symptom_types.join(', ')}` : ''}`}
                  className={`relative h-9 rounded-lg flex items-center justify-center text-xs cursor-default transition-colors ${classes} ${todayRing}`}
                >
                  {Number(day.date.slice(8))}
                  {day.has_symptom && (
                    <span className="absolute bottom-1 w-1 h-1 rounded-full bg-accent" />
                  )}
                </div>
              )
            })}
          </div>

          <div className="flex flex-wrap gap-x-4 gap-y-2 mt-4 pt-3 border-t border-border">
            {legend.map(item => (
              <div key={item.label} className="flex items-center gap-1.5">
                <span className={`w-2.5 h-2.5 rounded-sm ${item.color}`} />
                <span className="text-text-muted text-[10px]">{item.label}</span>
              </div>
            ))}
          </div>
        </Card>

        {/* Cycle Insights */}
        <section>
          <h2 className="text-text-primary font-semibold text-sm mb-3">{t['womens.insights']}</h2>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {stats.map(s => {
              const Icon = s.icon
              return (
                <Card key={s.label} padding="md">
                  <div className="flex items-center gap-2 mb-2">
                    <Icon size={14} className={s.color} />
                    <span className="text-text-secondary text-xs">{s.label}</span>
                  </div>
                  <p className="text-text-primary text-xl font-bold leading-none">{s.value}</p>
                  {s.unit && <p className="text-text-muted text-xs mt-1">{s.unit}</p>}
                </Card>
              )
            })}
          </div>
        </section>

        {/* Recent Symptoms + Cycle History */}
        <div className="grid lg:grid-cols-2 gap-6">
          <Card>
            <h3 className="text-text-primary font-semibold text-sm mb-3">{t['womens.recent_symptoms']}</h3>
            {symptoms.length === 0 ? (
              <p className="text-text-muted text-xs py-4 text-center">{t['womens.no_symptoms']}</p>
            ) : (
              <div>
                {symptoms.slice(0, 8).map(s => (
                  <div key={s.id} className="flex items-center justify-between py-2 border-b border-border last:border-b-0">
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div className="w-7 h-7 rounded-lg bg-[#EC4899]/10 border border-[#EC4899]/20 flex items-center justify-center shrink-0">
                        <Heart size={12} className="text-[#F472B6]" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-text-primary text-xs font-medium truncate">
                          {t[`womens.symptom_${s.symptom_type}` as keyof typeof t]}
                        </p>
                        <p className="text-text-muted text-[10px]">{fmtDate(s.date)}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <Badge label={t[`womens.severity_${s.severity}` as keyof typeof t]} variant={severityBadgeVariant[s.severity]} />
                      <button
                        type="button"
                        onClick={() => handleDeleteSymptom(s.id)}
                        disabled={deletingId === s.id}
                        className="text-text-muted hover:text-danger transition-colors disabled:opacity-50"
                        aria-label="Delete symptom"
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>

          <Card padding="none">
            <div className="p-5 pb-3">
              <h3 className="text-text-primary font-semibold text-sm">{t['womens.history']}</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-y border-border text-text-muted">
                    <th className="text-left font-medium px-5 py-2">{t['womens.col_start']}</th>
                    <th className="text-center font-medium px-3 py-2">{t['womens.col_end']}</th>
                    <th className="text-center font-medium px-3 py-2">{t['womens.col_cycle_length']}</th>
                    <th className="text-center font-medium px-5 py-2">{t['womens.col_period_length']}</th>
                  </tr>
                </thead>
                <tbody>
                  {cycles.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="text-center text-text-muted py-6">{t['womens.no_cycles']}</td>
                    </tr>
                  ) : (
                    cycles.map(c => (
                      <tr key={c.id} className="border-b border-border last:border-b-0">
                        <td className="px-5 py-2.5 text-text-primary whitespace-nowrap">{fmtDate(c.start_date)}</td>
                        <td className="px-3 py-2.5 text-center whitespace-nowrap">
                          {c.end_date ? (
                            <span className="text-text-secondary">{fmtDate(c.end_date)}</span>
                          ) : (
                            <Badge label={t['womens.ongoing']} variant="info" />
                          )}
                        </td>
                        <td className="px-3 py-2.5 text-center text-text-secondary">
                          {c.cycle_length != null ? `${c.cycle_length} ${t['womens.days_unit']}` : '—'}
                        </td>
                        <td className="px-5 py-2.5 text-center text-text-secondary">
                          {c.period_length != null ? `${c.period_length} ${t['womens.days_unit']}` : '—'}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        </div>

        {/* Safety note */}
        <div className="flex items-start gap-2 text-text-muted text-xs bg-bg-surface border border-border rounded-xl p-4">
          <Info size={14} className="shrink-0 mt-0.5 text-primary" />
          <p className="italic leading-relaxed">{t['womens.safety_note']}</p>
        </div>

      </div>
    </PageWrapper>
  )
}
