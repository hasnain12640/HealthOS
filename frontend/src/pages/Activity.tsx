import { useEffect, useState } from 'react'
import { PageWrapper, Card, Spinner } from '../components/ui'
import { getAnalysis, type SleepAnalysis, type ActivityAnalysis } from '../services/analysisService'
import { Activity, Moon } from 'lucide-react'

export function ActivityPage() {
  const [sleep, setSleep] = useState<SleepAnalysis | null>(null)
  const [activity, setActivity] = useState<ActivityAnalysis | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    getAnalysis()
      .then(r => { setSleep(r.sleep); setActivity(r.activity) })
      .catch(() => setError('Could not load activity data. Is the backend running?'))
  }, [])

  if (error) return (
    <PageWrapper title="Activity & Sleep" subtitle="Physical activity and sleep tracking">
      <Card><p className="text-[#EF4444] text-sm text-center py-4">{error}</p></Card>
    </PageWrapper>
  )

  if (!sleep || !activity) return (
    <PageWrapper title="Activity & Sleep" subtitle="Physical activity and sleep tracking">
      <div className="flex justify-center py-12"><Spinner size="lg" /></div>
    </PageWrapper>
  )

  const sleepStatusColor = sleep.status === 'good' ? '#10B981' : sleep.status === 'fair' ? '#F59E0B' : '#EF4444'
  const activityColor = activity.status === 'good' ? '#10B981' : activity.status === 'fair' ? '#F59E0B' : '#EF4444'

  return (
    <PageWrapper title="Activity & Sleep" subtitle="Physical activity and sleep tracking">
      <div className="space-y-4">
        {/* Sleep summary */}
        <Card>
          <h3 className="text-[#F9FAFB] font-semibold text-sm mb-3 flex items-center gap-2">
            <Moon size={14} className="text-[#A78BFA]" /> Sleep (Last 7 Days)
          </h3>
          <div className="flex items-center gap-6 mb-3">
            <div>
              <p className="text-[#F9FAFB] font-bold text-2xl">{sleep.avg_hours}h</p>
              <p className="text-[#9CA3AF] text-xs">7-day average</p>
            </div>
            <div>
              <p className="font-semibold text-sm" style={{ color: sleepStatusColor }}>{sleep.label}</p>
              <p className="text-[#6B7280] text-xs">
                Recommended: {sleep.target_hours}–9 hours
                {sleep.deficit_hours > 0 && ` · ${sleep.deficit_hours}h deficit`}
              </p>
            </div>
          </div>
          {/* Bar chart */}
          <div className="flex items-end gap-1 h-16">
            {sleep.logs.map((s, i) => {
              const h = s.hours_slept
              const pct = Math.round((h / 9) * 100)
              const color = h >= 7 ? '#10B981' : h >= 6 ? '#F59E0B' : '#EF4444'
              return (
                <div key={i} className="flex-1 flex flex-col items-center gap-1">
                  <div className="w-full rounded-t" style={{ height: `${pct}%`, backgroundColor: color, minHeight: '4px' }} />
                  <span className="text-[#6B7280] text-[10px]">{h}h</span>
                </div>
              )
            })}
          </div>
        </Card>

        {/* Activity summary */}
        <Card>
          <h3 className="text-[#F9FAFB] font-semibold text-sm mb-3 flex items-center gap-2">
            <Activity size={14} className="text-[#10B981]" /> Weekly Activity
          </h3>
          <div className="flex items-center justify-between mb-3">
            <div>
              <p className="text-[#F9FAFB] font-bold text-xl">{activity.total_minutes} min</p>
              <p className="text-[#9CA3AF] text-xs">of {activity.weekly_target_min} min target this week</p>
            </div>
            <div className="text-right">
              <p className="font-bold text-xl" style={{ color: activityColor }}>{activity.percent}%</p>
              <p className="text-xs" style={{ color: activityColor }}>{activity.label}</p>
            </div>
          </div>
          <div className="h-2 bg-[#1F2937] rounded-full overflow-hidden mb-4">
            <div className="h-full rounded-full" style={{ width: `${Math.min(activity.percent, 100)}%`, backgroundColor: activityColor }} />
          </div>

          {/* Activity log */}
          <div className="space-y-2">
            {activity.recent.map(a => (
              <div key={a.id} className="flex items-center justify-between bg-[#1F2937] rounded-lg px-3 py-2">
                <div>
                  <p className="text-[#F9FAFB] text-sm capitalize">{a.activity_type}</p>
                  <p className="text-[#6B7280] text-xs">{a.date}</p>
                </div>
                <div className="text-right">
                  <p className="text-[#F9FAFB] text-sm">{a.duration_min} min</p>
                  <p className="text-[#6B7280] text-xs">{a.steps.toLocaleString()} steps</p>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card padding="sm">
          <p className="text-[#6B7280] text-xs text-center">
            Activity target based on WHO guideline of 150 minutes of moderate activity per week. This is a general guideline, not medical advice.
          </p>
        </Card>
      </div>
    </PageWrapper>
  )
}
