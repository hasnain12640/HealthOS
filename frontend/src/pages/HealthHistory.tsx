import { useEffect, useMemo, useState } from 'react'
import { PageWrapper, Card, Badge, Spinner, Button } from '../components/ui'
import { getHistory, type HistoryData, type HistoryDay } from '../services/historyService'
import { useT } from '../i18n/useT'
import {
  Activity, AlertTriangle, Apple, Beaker, Brain, CalendarDays, CheckCircle2,
  Clock, Droplets, FlaskConical, Footprints, Heart, HeartPulse, Moon, Watch,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from 'recharts'

const eventIcons: Record<string, LucideIcon> = {
  lab: FlaskConical,
  nutrition: Apple,
  hydration: Droplets,
  ai_insight: Brain,
  plan: CalendarDays,
  activity: Activity,
  wearable: Watch,
  cycle: Heart,
  cycle_symptom: HeartPulse,
}

function formatDateShort(iso: string) {
  const d = new Date(`${iso}T00:00:00`)
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

function formatDateLong(iso: string) {
  const d = new Date(`${iso}T00:00:00`)
  return d.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })
}

function weekStartLabel(iso: string) {
  const d = new Date(`${iso}T00:00:00`)
  const start = new Date(d)
  start.setDate(d.getDate() - d.getDay())
  return start.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

function isDayEmpty(day: HistoryDay) {
  const { wearable, hydration, sleep, activity, nutrition, labs, events, cycle } = day
  if (wearable.steps != null && wearable.steps > 0) return false
  if (wearable.active_calories != null) return false
  if (wearable.resting_heart_rate != null) return false
  if (wearable.avg_heart_rate != null) return false
  if (wearable.sleep_hours != null) return false
  if (wearable.distance_km != null) return false
  if (wearable.water_ml != null) return false
  if (wearable.weight_kg != null) return false
  if (hydration.amount_ml > 0) return false
  if (sleep) return false
  if (activity.duration_min > 0 || activity.steps > 0) return false
  if (nutrition.meal_count > 0) return false
  if (labs.length > 0) return false
  if (events.length > 0) return false
  if (cycle && (cycle.phase || cycle.symptoms.length > 0)) return false
  return true
}

function StatCard({ icon: Icon, label, value, detail, tone = 'primary' }: {
  icon: LucideIcon
  label: string
  value: string
  detail: string
  tone?: 'primary' | 'violet' | 'cyan' | 'green' | 'rose'
}) {
  const toneClass = {
    primary: 'border-primary/25 bg-primary/10 text-primary',
    violet: 'border-primary-light/25 bg-primary-light/10 text-primary-light',
    cyan: 'border-primary-light/25 bg-primary-light/10 text-primary-light',
    green: 'border-accent/25 bg-accent/10 text-accent',
    rose: 'border-danger/25 bg-danger/10 text-danger',
  }[tone]

  return (
    <div className="dashboard-glass dashboard-hover rounded-2xl border border-border p-4">
      <div className="flex items-center justify-between gap-3">
        <span className={`flex h-9 w-9 items-center justify-center rounded-xl border ${toneClass}`}><Icon size={16} /></span>
        <span className="text-[10px] uppercase tracking-[0.14em] text-text-muted">{label}</span>
      </div>
      <p className="mt-4 text-2xl font-semibold tracking-tight text-text-primary">{value}</p>
      <p className="mt-1 text-xs text-text-secondary">{detail}</p>
    </div>
  )
}

function DaySection({ title, children, isEmpty }: { title: string; children: React.ReactNode; isEmpty?: boolean }) {
  if (isEmpty) return null
  return (
    <div className="border-t border-border pt-3 mt-3 first:border-t-0 first:pt-0 first:mt-0">
      <h4 className="text-[10px] uppercase tracking-[0.14em] text-text-muted mb-2">{title}</h4>
      {children}
    </div>
  )
}

export function HealthHistory() {
  const t = useT()
  const [data, setData] = useState<HistoryData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const history = await getHistory(30)
      setData(history)
    } catch {
      setError(t['common.backend_not_reachable'])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { void load() }, [])

  const chartData = useMemo(() => {
    if (!data) return []
    return data.daily.map(day => ({
      date: formatDateShort(day.date),
      steps: day.wearable.steps ?? 0,
      sleep: day.sleep?.hours_slept ?? 0,
      hydration: day.hydration.percent,
    }))
  }, [data])

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
        <Button variant="secondary" size="sm" onClick={() => void load()}>{t['common.retry']}</Button>
      </div>
    )
  }

  const { summary, wearable, daily, profile } = data
  const reversedDays = [...daily].reverse()
  const isFemale = profile.sex === 'female'

  return (
    <PageWrapper title={t['history.title']} subtitle={t['history.subtitle'].replace('{{days}}', '30')}>
      <div className="space-y-5 pb-4">
        {/* Summary cards */}
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <StatCard icon={Footprints} label={t['history.avg_steps']} value={summary.avg_steps.toLocaleString()} detail={t['history.last_30_days']} tone="primary" />
          <StatCard icon={Moon} label={t['history.avg_sleep']} value={`${summary.avg_sleep_hours}h`} detail={t['history.last_30_days']} tone="violet" />
          <StatCard icon={Droplets} label={t['history.avg_hydration']} value={`${summary.avg_hydration_percent}%`} detail={`${Math.round(summary.avg_hydration_ml)} ml/day`} tone="cyan" />
          <StatCard icon={Activity} label={t['history.activity']} value={`${summary.total_activity_minutes}`} detail={t['history.total_minutes']} tone="green" />
        </div>

        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <StatCard icon={FlaskConical} label={t['history.lab_reports']} value={String(summary.total_reports)} detail={`${summary.total_biomarkers} ${t['history.biomarkers']}`} tone="primary" />
          <StatCard icon={Beaker} label={t['history.abnormal']} value={String(summary.abnormal_biomarker_count)} detail={t['history.outside_range']} tone="rose" />
          {isFemale && (
            <StatCard icon={Heart} label={t['history.period_days']} value={String(summary.period_days)} detail={t['history.in_window']} tone="rose" />
          )}
          {summary.ai_insight?.text && (
            <StatCard icon={Brain} label={t['history.ai_insight']} value="1" detail={new Date(summary.ai_insight.date).toLocaleDateString()} tone="violet" />
          )}
        </div>

        {/* Trend chart */}
        <Card>
          <div className="flex items-center gap-2 mb-4">
            <Activity size={14} className="text-primary" />
            <h3 className="text-text-primary font-semibold text-sm">{t['history.trends']}</h3>
          </div>
          <div className="h-64 -ml-2">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 5, right: 5, left: -15, bottom: 0 }}>
                <defs>
                  <linearGradient id="stepsGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--color-primary)" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="var(--color-primary)" stopOpacity={0.02} />
                  </linearGradient>
                  <linearGradient id="hydrationGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--color-accent)" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="var(--color-accent)" stopOpacity={0.02} />
                  </linearGradient>
                  <linearGradient id="sleepGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--color-primary-light)" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="var(--color-primary-light)" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-subtle)" vertical={false} />
                <XAxis dataKey="date" tick={{ fill: 'var(--color-text-muted)', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis yAxisId="left" tick={{ fill: 'var(--color-text-muted)', fontSize: 10 }} axisLine={false} tickLine={false} width={45} />
                <YAxis yAxisId="right" orientation="right" tick={{ fill: 'var(--color-text-muted)', fontSize: 10 }} axisLine={false} tickLine={false} width={30} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'var(--color-bg-surface)',
                    border: '1px solid var(--color-border)',
                    borderRadius: '8px',
                    fontSize: '12px',
                  }}
                  labelStyle={{ color: 'var(--color-text-secondary)' }}
                  itemStyle={{ color: 'var(--color-text-primary)' }}
                />
                <Area yAxisId="left" type="monotone" dataKey="steps" name={t['history.steps']} stroke="var(--color-primary)" strokeWidth={2} fill="url(#stepsGradient)" />
                <Area yAxisId="right" type="monotone" dataKey="hydration" name={t['history.hydration_pct']} stroke="var(--color-accent)" strokeWidth={2} fill="url(#hydrationGradient)" />
                <Area yAxisId="right" type="monotone" dataKey="sleep" name={t['history.sleep_hours']} stroke="var(--color-primary-light)" strokeWidth={2} fill="url(#sleepGradient)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-text-secondary">
            <span className="inline-flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-primary" />{t['history.steps']}</span>
            <span className="inline-flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-accent" />{t['history.hydration_pct']}</span>
            <span className="inline-flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-primary-light" />{t['history.sleep_hours']}</span>
          </div>
        </Card>

        {/* Device info */}
        {wearable && (
          <div className="flex items-center gap-2 text-xs text-text-secondary">
            <Watch size={14} className="text-primary" />
            <span>{wearable.device_name} · {t['wearables.last_synced']} {new Date(wearable.last_synced_at).toLocaleString()}</span>
          </div>
        )}

        {/* Priorities */}
        {summary.priorities.length > 0 && (
          <Card>
            <h3 className="text-text-primary font-semibold text-sm mb-3">{t['dashboard.health_priorities']}</h3>
            <div className="space-y-2.5">
              {summary.priorities.map(priority => (
                <div key={priority.id} className="rounded-2xl border border-border bg-bg-base/40 p-3.5">
                  <div className="flex items-start justify-between gap-3">
                    <p className="text-xs font-semibold leading-relaxed text-text-primary">{priority.title}</p>
                    <Badge
                      label={priority.severity === 'high' ? t['insight.urgency_high'] : priority.severity === 'medium' ? t['insight.urgency_medium'] : t['insight.urgency_low']}
                      variant={priority.severity === 'high' ? 'high' : priority.severity === 'medium' ? 'low' : 'normal'}
                      size="sm"
                    />
                  </div>
                  <p className="mt-2 text-xs leading-relaxed text-text-secondary">{priority.observed_data}</p>
                  <p className="mt-2 rounded-lg border border-accent/15 bg-accent/5 px-2.5 py-2 text-xs leading-relaxed text-text-secondary">{priority.suggested_action}</p>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* AI insight */}
        {summary.ai_insight?.text && (
          <Card>
            <div className="flex items-center gap-2 mb-2">
              <Brain size={14} className="text-primary-light" />
              <h3 className="text-text-primary font-semibold text-sm">{t['dashboard.latest_ai_insight']}</h3>
              <span className="text-[10px] font-medium px-1.5 py-0.5 rounded-full border text-primary-light bg-primary-light/10 border-primary-light/20">AI</span>
            </div>
            <p className="text-xs text-text-secondary leading-relaxed">{summary.ai_insight.text}</p>
            <p className="text-text-muted text-[10px] mt-2 italic">{t['dashboard.ai_disclaimer']}</p>
          </Card>
        )}

        {/* Daily detail grouped by week, empty days hidden */}
        <section>
          <h3 className="text-text-primary font-semibold text-sm mb-3">{t['history.daily_detail']}</h3>
          <div className="space-y-5">
            {Object.entries(
              reversedDays.reduce<Record<string, HistoryDay[]>>((acc, day) => {
                const key = weekStartLabel(day.date)
                if (!acc[key]) acc[key] = []
                acc[key].push(day)
                return acc
              }, {})
            ).map(([weekLabel, days]) => {
              const visibleDays = days.filter(d => !isDayEmpty(d))
              if (visibleDays.length === 0) return null
              return (
                <Card key={weekLabel} padding="md">
                  <h4 className="text-text-secondary text-xs font-medium uppercase tracking-wider mb-3">
                    {t['history.week_of'].replace('{{date}}', weekLabel)}
                  </h4>
                  <div className="space-y-3">
                    {visibleDays.map(day => (
                      <DayCard key={day.date} day={day} isFemale={isFemale} />
                    ))}
                  </div>
                </Card>
              )
            })}
          </div>
        </section>
      </div>
    </PageWrapper>
  )
}

function DayCard({ day, isFemale }: { day: HistoryDay; isFemale: boolean }) {
  const t = useT()
  const { wearable, hydration, sleep, activity, nutrition, labs, events, cycle } = day

  return (
    <Card className={day.is_today ? 'border-primary/30' : ''}>
      <div className="flex items-start justify-between gap-3 mb-3">
        <div>
          <h4 className="text-text-primary font-medium text-sm">{formatDateLong(day.date)}</h4>
          {day.is_today && <Badge label={t['dashboard.today']} variant="info" size="sm" />}
        </div>
        <div className="flex flex-wrap justify-end gap-1.5">
          {wearable.steps != null && wearable.steps > 0 && (
            <span className="inline-flex items-center gap-1 text-[10px] text-text-secondary bg-bg-elevated rounded-full px-2 py-0.5">
              <Footprints size={10} className="text-primary" />{wearable.steps.toLocaleString()}
            </span>
          )}
          {sleep && (
            <span className="inline-flex items-center gap-1 text-[10px] text-text-secondary bg-bg-elevated rounded-full px-2 py-0.5">
              <Moon size={10} className="text-primary-light" />{sleep.hours_slept}h
            </span>
          )}
          {nutrition.total_calories > 0 && (
            <span className="inline-flex items-center gap-1 text-[10px] text-text-secondary bg-bg-elevated rounded-full px-2 py-0.5">
              <Apple size={10} className="text-accent" />{nutrition.total_calories}
            </span>
          )}
        </div>
      </div>

      <DaySection title={t['history.wearable']} isEmpty={
        wearable.steps == null && wearable.active_calories == null && wearable.sleep_hours == null
      }>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          {wearable.steps != null && <MetricPill icon={Footprints} label={t['wearables.metric_steps']} value={wearable.steps.toLocaleString()} />}
          {wearable.active_calories != null && <MetricPill icon={Activity} label={t['wearables.metric_active_calories']} value={`${wearable.active_calories} kcal`} />}
          {wearable.resting_heart_rate != null && <MetricPill icon={Heart} label={t['wearables.metric_resting_heart_rate']} value={`${wearable.resting_heart_rate} bpm`} />}
          {wearable.avg_heart_rate != null && <MetricPill icon={Heart} label={t['wearables.metric_avg_heart_rate']} value={`${wearable.avg_heart_rate} bpm`} />}
          {wearable.sleep_hours != null && <MetricPill icon={Moon} label={t['wearables.metric_sleep']} value={`${wearable.sleep_hours}h`} />}
          {wearable.distance_km != null && <MetricPill icon={Activity} label={t['wearables.metric_distance']} value={`${wearable.distance_km} km`} />}
          {wearable.water_ml != null && <MetricPill icon={Droplets} label={t['wearables.metric_water']} value={`${wearable.water_ml} ml`} />}
          {wearable.weight_kg != null && <MetricPill icon={Activity} label={t['wearables.metric_weight']} value={`${wearable.weight_kg} kg`} />}
        </div>
      </DaySection>

      <DaySection title={t['history.hydration']} isEmpty={hydration.amount_ml === 0}>
        <div className="flex items-center justify-between gap-3">
          <span className="text-text-secondary text-xs">{hydration.amount_ml} ml {t['common.of']} {hydration.target_ml} ml</span>
          <Badge label={`${hydration.percent}%`} variant={hydration.status === 'good' ? 'normal' : hydration.status === 'moderate' ? 'low' : 'high'} size="sm" />
        </div>
        <div className="mt-2 h-1.5 bg-bg-elevated rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{
              width: `${Math.min(hydration.percent, 100)}%`,
              backgroundColor: hydration.percent >= 80 ? 'var(--color-status-normal)' : hydration.percent >= 50 ? 'var(--color-status-low)' : 'var(--color-status-high)',
            }}
          />
        </div>
      </DaySection>

      {sleep && (
        <DaySection title={t['history.sleep']}>
          <div className="flex items-center gap-3">
            <MetricPill icon={Moon} label={t['history.hours_slept']} value={`${sleep.hours_slept}h`} />
            <MetricPill icon={CheckCircle2} label={t['history.quality']} value={`${sleep.quality}/5`} />
            <Badge label={sleep.label} variant={sleep.status === 'good' ? 'normal' : 'low'} size="sm" />
          </div>
        </DaySection>
      )}

      <DaySection title={t['history.activity']} isEmpty={activity.duration_min === 0 && activity.steps === 0}>
        <div className="flex items-center gap-3">
          <MetricPill icon={Footprints} label={t['wearables.metric_steps']} value={activity.steps.toLocaleString()} />
          <MetricPill icon={Clock} label={t['history.duration']} value={`${activity.duration_min} min`} />
          <MetricPill icon={Activity} label={t['history.sessions']} value={String(activity.sessions)} />
        </div>
      </DaySection>

      <DaySection title={t['history.nutrition']} isEmpty={nutrition.meal_count === 0}>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          <MetricPill icon={Apple} label={t['history.calories']} value={String(nutrition.total_calories)} />
          <MetricPill icon={Activity} label={t['history.protein']} value={`${Math.round(nutrition.total_protein_g)}g`} />
          <MetricPill icon={Activity} label={t['history.carbs']} value={`${Math.round(nutrition.total_carbs_g)}g`} />
          <MetricPill icon={Activity} label={t['history.fat']} value={`${Math.round(nutrition.total_fat_g)}g`} />
        </div>
      </DaySection>

      <DaySection title={t['history.labs']} isEmpty={labs.length === 0}>
        <div className="space-y-2">
          {labs.map(report => (
            <div key={report.id} className="rounded-lg border border-border-subtle bg-bg-base/40 p-2.5">
              <p className="text-text-primary text-xs font-medium">{report.lab_name}</p>
              <div className="mt-1.5 flex flex-wrap gap-1.5">
                {report.biomarkers.map(bm => (
                  <Badge key={bm.id} label={`${bm.name}: ${bm.value} ${bm.unit}`} variant={bm.status} size="sm" />
                ))}
              </div>
            </div>
          ))}
        </div>
      </DaySection>

      <DaySection title={t['dashboard.health_timeline']} isEmpty={events.length === 0}>
        <div className="space-y-2">
          {events.map(event => {
            const Icon = eventIcons[event.event_type] ?? Activity
            return (
              <div key={event.id} className="flex items-start gap-2 text-xs">
                <Icon size={12} className="text-text-muted mt-0.5 shrink-0" />
                <div>
                  <p className="text-text-primary font-medium">{event.title}</p>
                  <p className="text-text-secondary">{event.description}</p>
                </div>
              </div>
            )
          })}
        </div>
      </DaySection>

      {isFemale && cycle && (
        <DaySection title={t['history.cycle']}>
          <div className="flex flex-wrap items-center gap-2">
            <Badge label={cycle.phase} variant="info" size="sm" />
            <span className="text-text-secondary text-xs">{t['womens.day_of'].replace('{{day}}', String(cycle.cycle_day)).replace('{{total}}', '?')}</span>
            {cycle.is_period && <Badge label={t['womens.legend_period']} variant="high" size="sm" />}
            {cycle.is_fertile_window && <Badge label={t['womens.legend_fertile']} variant="low" size="sm" />}
          </div>
          {cycle.symptoms.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {cycle.symptoms.map(s => <Badge key={s} label={t[`womens.symptom_${s}` as keyof typeof t] ?? s} variant="default" size="sm" />)}
            </div>
          )}
        </DaySection>
      )}
    </Card>
  )
}

function MetricPill({ icon: Icon, label, value }: { icon: LucideIcon; label: string; value: string }) {
  return (
    <div className="rounded-xl bg-bg-base/45 px-2.5 py-2">
      <div className="flex items-center gap-1.5 text-text-muted"><Icon size={11} className="text-primary" /><span className="truncate text-[10px]">{label}</span></div>
      <p className="mt-1 truncate text-xs font-semibold text-text-primary" title={value}>{value}</p>
    </div>
  )
}
