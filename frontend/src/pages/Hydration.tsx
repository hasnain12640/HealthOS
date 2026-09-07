import { useEffect, useState } from 'react'
import { PageWrapper, Card } from '../components/ui'
import { Spinner } from '../components/ui'
import { getAnalysis, type HydrationAnalysis } from '../services/analysisService'
import { Droplets } from 'lucide-react'

export function Hydration() {
  const [data, setData] = useState<HydrationAnalysis | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    getAnalysis()
      .then(r => setData(r.hydration))
      .catch(() => setError('Could not load hydration data. Is the backend running?'))
  }, [])

  if (error) return (
    <PageWrapper title="Hydration" subtitle="Daily water intake tracking">
      <Card><p className="text-danger text-sm text-center py-4">{error}</p></Card>
    </PageWrapper>
  )

  if (!data) return (
    <PageWrapper title="Hydration" subtitle="Daily water intake tracking">
      <div className="flex justify-center py-12"><Spinner size="lg" /></div>
    </PageWrapper>
  )

  const barColor = data.percent >= 90 ? 'var(--color-status-normal)' : data.percent >= 60 ? 'var(--color-status-low)' : 'var(--color-status-high)'

  return (
    <PageWrapper title="Hydration" subtitle="Daily water intake tracking">
      <div className="space-y-4">
        {/* Progress bar */}
        <Card>
          <div className="flex items-center justify-between mb-3">
            <div>
              <p className="text-text-primary font-semibold text-lg">{data.today_ml} ml</p>
              <p className="text-text-secondary text-sm">of {data.target_ml} ml daily target</p>
            </div>
            <div className="text-right">
              <p className="font-bold text-2xl" style={{ color: barColor }}>{data.percent}%</p>
              <p className="text-text-muted text-xs">{data.label}</p>
            </div>
          </div>
          <div className="h-3 bg-bg-elevated rounded-full overflow-hidden">
            <div className="h-full rounded-full transition-all" style={{ width: `${Math.min(data.percent, 100)}%`, backgroundColor: barColor }} />
          </div>
          <p className="text-text-muted text-xs mt-2">
            {data.remaining_ml > 0
              ? `${data.remaining_ml} ml remaining to reach your daily target.`
              : 'You have met your hydration target today.'}
          </p>
        </Card>

        {/* Weekly average */}
        <Card padding="sm">
          <div className="flex items-center justify-between">
            <span className="text-text-secondary text-sm">Weekly average</span>
            <span className="text-text-primary font-medium text-sm">{data.weekly_avg_ml} ml / day</span>
          </div>
        </Card>

        {/* Today's logs */}
        <Card>
          <h3 className="text-text-primary font-semibold text-sm mb-3 flex items-center gap-2">
            <Droplets size={14} className="text-primary" /> Today's Intake
          </h3>
          <div className="space-y-2">
            {data.logs_today.map(l => (
              <div key={l.id} className="flex items-center justify-between bg-bg-elevated rounded-lg px-3 py-2">
                <div className="flex items-center gap-2">
                  <Droplets size={14} className="text-primary-light" />
                  <span className="text-text-primary text-sm capitalize">{l.source}</span>
                </div>
                <span className="text-text-secondary text-sm">{l.amount_ml} ml</span>
              </div>
            ))}
          </div>
        </Card>

        <Card padding="sm">
          <p className="text-text-muted text-xs text-center">
            Hydration target is calculated based on your body weight (32 ml per kg). This is a general guideline, not medical advice.
          </p>
        </Card>
      </div>
    </PageWrapper>
  )
}
