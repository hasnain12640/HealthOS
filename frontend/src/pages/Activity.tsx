import { useCallback, useEffect, useState } from 'react'
import { Button, Card, PageWrapper, Spinner } from '../components/ui'
import { Activity, CirclePlus, Moon } from 'lucide-react'
import { ManualLifestyleEntryModal, type LifestyleEntryType } from '../components/lifestyle/ManualLifestyleEntryModal'
import { getAnalysis, type ActivityAnalysis, type SleepAnalysis } from '../services/analysisService'
import { useT } from '../i18n/useT'

export function ActivityPage() {
  const [sleep, setSleep] = useState<SleepAnalysis | null>(null)
  const [activity, setActivity] = useState<ActivityAnalysis | null>(null)
  const [error, setError] = useState('')
  const [entryType, setEntryType] = useState<LifestyleEntryType | null>(null)
  const t = useT()

  const loadData = useCallback(async () => {
    setError('')
    try {
      const analysis = await getAnalysis()
      setSleep(analysis.sleep)
      setActivity(analysis.activity)
    } catch {
      setError('Could not load activity data. Is the backend running?')
    }
  }, [])

  useEffect(() => {
    void loadData()
  }, [loadData])

  const action = (
    <div className="flex flex-wrap justify-end gap-2">
      <Button size="sm" variant="secondary" onClick={() => setEntryType('sleep')}><Moon size={15} />{t['lifestyle.log_sleep']}</Button>
      <Button size="sm" onClick={() => setEntryType('activity')}><CirclePlus size={15} />{t['lifestyle.log_activity']}</Button>
    </div>
  )

  return (
    <>
      <PageWrapper title="Activity & Sleep" subtitle="Physical activity and sleep tracking" action={action}>
        {error ? (
          <Card><p className="py-4 text-center text-sm text-danger">{error}</p></Card>
        ) : !sleep || !activity ? (
          <div className="flex justify-center py-12"><Spinner size="lg" /></div>
        ) : (
          <ActivityContent sleep={sleep} activity={activity} />
        )}
      </PageWrapper>
      <ManualLifestyleEntryModal open={entryType !== null} entryType={entryType ?? 'activity'} onClose={() => setEntryType(null)} onSuccess={loadData} />
    </>
  )
}

function ActivityContent({ sleep, activity }: { sleep: SleepAnalysis; activity: ActivityAnalysis }) {
  const sleepStatusColor = sleep.status === 'good' ? 'var(--color-status-normal)' : sleep.status === 'fair' ? 'var(--color-status-low)' : 'var(--color-status-high)'
  const activityColor = activity.status === 'good' ? 'var(--color-status-normal)' : activity.status === 'fair' ? 'var(--color-status-low)' : 'var(--color-status-high)'

  return (
    <div className="space-y-4">
      <Card>
        <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-text-primary"><Moon size={14} className="text-primary-light" /> Sleep (Last 7 Days)</h3>
        <div className="mb-3 flex items-center gap-6">
          <div>
            <p className="text-2xl font-bold text-text-primary">{sleep.avg_hours}h</p>
            <p className="text-xs text-text-secondary">7-day average</p>
          </div>
          <div>
            <p className="text-sm font-semibold" style={{ color: sleepStatusColor }}>{sleep.label}</p>
            <p className="text-xs text-text-muted">Recommended: {sleep.target_hours}–9 hours{sleep.deficit_hours > 0 && ` · ${sleep.deficit_hours}h deficit`}</p>
          </div>
        </div>
        <div className="flex h-16 items-end gap-1">
          {sleep.logs.map((log, index) => {
            const height = Math.round((log.hours_slept / 9) * 100)
            const color = log.hours_slept >= 7 ? 'var(--color-status-normal)' : log.hours_slept >= 6 ? 'var(--color-status-low)' : 'var(--color-status-high)'
            return (
              <div key={`${log.date}-${index}`} className="flex flex-1 flex-col items-center gap-1">
                <div className="w-full rounded-t" style={{ height: `${height}%`, backgroundColor: color, minHeight: '4px' }} />
                <span className="text-[10px] text-text-muted">{log.hours_slept}h</span>
              </div>
            )
          })}
        </div>
      </Card>

      <Card>
        <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-text-primary"><Activity size={14} className="text-accent" /> Weekly Activity</h3>
        <div className="mb-3 flex items-center justify-between">
          <div>
            <p className="text-xl font-bold text-text-primary">{activity.total_minutes} min</p>
            <p className="text-xs text-text-secondary">of {activity.weekly_target_min} min target this week</p>
          </div>
          <div className="text-right">
            <p className="text-xl font-bold" style={{ color: activityColor }}>{activity.percent}%</p>
            <p className="text-xs" style={{ color: activityColor }}>{activity.label}</p>
          </div>
        </div>
        <div className="mb-4 h-2 overflow-hidden rounded-full bg-bg-elevated">
          <div className="h-full rounded-full" style={{ width: `${Math.min(activity.percent, 100)}%`, backgroundColor: activityColor }} />
        </div>
        <div className="space-y-2">
          {activity.recent.map(entry => (
            <div key={entry.id} className="flex items-center justify-between rounded-lg bg-bg-elevated px-3 py-2">
              <div className="min-w-0">
                <p className="truncate text-sm capitalize text-text-primary">{entry.activity_type}</p>
                <p className="text-xs text-text-muted">{entry.notes || entry.date}</p>
              </div>
              <div className="ml-3 shrink-0 text-right">
                <p className="text-sm text-text-primary">{entry.duration_min} min</p>
                <p className="text-xs text-text-muted">{entry.steps.toLocaleString()} steps</p>
              </div>
            </div>
          ))}
        </div>
      </Card>

      <Card padding="sm">
        <p className="text-center text-xs text-text-muted">Activity target based on WHO guideline of 150 minutes of moderate activity per week. This is a general guideline, not medical advice.</p>
      </Card>
    </div>
  )
}
