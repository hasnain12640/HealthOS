import { useCallback, useEffect, useState } from 'react'
import { Button, Card, PageWrapper, Spinner } from '../components/ui'
import { CirclePlus, Droplets } from 'lucide-react'
import { ManualLifestyleEntryModal } from '../components/lifestyle/ManualLifestyleEntryModal'
import { getAnalysis, type HydrationAnalysis } from '../services/analysisService'
import { useT } from '../i18n/useT'

export function Hydration() {
  const [data, setData] = useState<HydrationAnalysis | null>(null)
  const [error, setError] = useState('')
  const [entryOpen, setEntryOpen] = useState(false)
  const t = useT()

  const loadData = useCallback(async () => {
    setError('')
    try {
      const analysis = await getAnalysis()
      setData(analysis.hydration)
    } catch {
      setError('Could not load hydration data. Is the backend running?')
    }
  }, [])

  useEffect(() => {
    void loadData()
  }, [loadData])

  const action = <Button size="sm" onClick={() => setEntryOpen(true)}><CirclePlus size={15} />{t['lifestyle.log_hydration']}</Button>

  return (
    <>
      <PageWrapper title="Hydration" subtitle="Daily water intake tracking" action={action}>
        {error ? (
          <Card><p className="py-4 text-center text-sm text-danger">{error}</p></Card>
        ) : !data ? (
          <div className="flex justify-center py-12"><Spinner size="lg" /></div>
        ) : (
          <HydrationContent data={data} />
        )}
      </PageWrapper>
      <ManualLifestyleEntryModal open={entryOpen} entryType="hydration" onClose={() => setEntryOpen(false)} onSuccess={loadData} />
    </>
  )
}

function HydrationContent({ data }: { data: HydrationAnalysis }) {
  const barColor = data.percent >= 90 ? 'var(--color-status-normal)' : data.percent >= 60 ? 'var(--color-status-low)' : 'var(--color-status-high)'

  return (
    <div className="space-y-4">
      <Card>
        <div className="mb-3 flex items-center justify-between">
          <div>
            <p className="text-lg font-semibold text-text-primary">{data.today_ml} ml</p>
            <p className="text-sm text-text-secondary">of {data.target_ml} ml daily target</p>
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold" style={{ color: barColor }}>{data.percent}%</p>
            <p className="text-xs text-text-muted">{data.label}</p>
          </div>
        </div>
        <div className="h-3 overflow-hidden rounded-full bg-bg-elevated">
          <div className="h-full rounded-full transition-all" style={{ width: `${Math.min(data.percent, 100)}%`, backgroundColor: barColor }} />
        </div>
        <p className="mt-2 text-xs text-text-muted">
          {data.remaining_ml > 0
            ? `${data.remaining_ml} ml remaining to reach your daily target.`
            : 'You have met your hydration target today.'}
        </p>
      </Card>

      <Card padding="sm">
        <div className="flex items-center justify-between">
          <span className="text-sm text-text-secondary">Weekly average</span>
          <span className="text-sm font-medium text-text-primary">{data.weekly_avg_ml} ml / day</span>
        </div>
      </Card>

      <Card>
        <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-text-primary">
          <Droplets size={14} className="text-primary" /> Today's Intake
        </h3>
        <div className="space-y-2">
          {data.logs_today.map(log => (
            <div key={log.id} className="flex items-center justify-between rounded-lg bg-bg-elevated px-3 py-2">
              <div className="flex items-center gap-2">
                <Droplets size={14} className="text-primary-light" />
                <span className="text-sm capitalize text-text-primary">{log.source}</span>
              </div>
              <span className="text-sm text-text-secondary">{log.amount_ml} ml</span>
            </div>
          ))}
        </div>
      </Card>

      <Card padding="sm">
        <p className="text-center text-xs text-text-muted">
          Hydration target is calculated based on your body weight (32 ml per kg). This is a general guideline, not medical advice.
        </p>
      </Card>
    </div>
  )
}
