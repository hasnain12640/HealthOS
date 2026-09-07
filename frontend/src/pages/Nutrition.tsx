import { useCallback, useEffect, useState } from 'react'
import { Button, Card, PageWrapper, Spinner } from '../components/ui'
import { Apple, CirclePlus, TrendingUp } from 'lucide-react'
import { ManualLifestyleEntryModal } from '../components/lifestyle/ManualLifestyleEntryModal'
import { getAnalysis, type NutritionAnalysis } from '../services/analysisService'
import { useT } from '../i18n/useT'

export function Nutrition() {
  const [data, setData] = useState<NutritionAnalysis | null>(null)
  const [error, setError] = useState('')
  const [entryOpen, setEntryOpen] = useState(false)
  const t = useT()

  const loadData = useCallback(async () => {
    setError('')
    try {
      const analysis = await getAnalysis()
      setData(analysis.nutrition)
    } catch {
      setError('Could not load nutrition data. Is the backend running?')
    }
  }, [])

  useEffect(() => {
    void loadData()
  }, [loadData])

  const action = <Button size="sm" onClick={() => setEntryOpen(true)}><CirclePlus size={15} />{t['lifestyle.log_nutrition']}</Button>

  return (
    <>
      <PageWrapper title="Nutrition" subtitle="Daily food and nutrition tracking" action={action}>
        {error ? (
          <Card><p className="py-4 text-center text-sm text-danger">{error}</p></Card>
        ) : !data ? (
          <div className="flex justify-center py-12"><Spinner size="lg" /></div>
        ) : (
          <NutritionContent data={data} />
        )}
      </PageWrapper>
      <ManualLifestyleEntryModal open={entryOpen} entryType="nutrition" onClose={() => setEntryOpen(false)} onSuccess={loadData} />
    </>
  )
}

function NutritionContent({ data }: { data: NutritionAnalysis }) {
  const macros = [
    { label: 'Calories', value: `${data.total_calories} kcal`, target: `Target: ${data.calorie_target} kcal`, color: 'var(--color-warning)' },
    { label: 'Protein', value: `${data.total_protein_g}g`, target: `Target: ${data.protein_target_g}g`, color: 'var(--color-primary)' },
    { label: 'Carbohydrates', value: `${data.total_carbs_g}g`, target: '', color: 'var(--color-accent)' },
    { label: 'Fat', value: `${data.total_fat_g}g`, target: '', color: 'var(--color-status-high)' },
  ]
  const calStatusColor = data.calorie_status === 'good' ? 'var(--color-status-normal)' : data.calorie_status === 'low' ? 'var(--color-status-low)' : 'var(--color-status-high)'

  return (
    <div className="space-y-4">
      <Card padding="sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <TrendingUp size={14} style={{ color: calStatusColor }} />
            <span className="text-sm font-medium text-text-primary">Calorie intake: {data.calorie_percent}% of target</span>
          </div>
          <span className="rounded-full px-2 py-0.5 text-xs" style={{ color: calStatusColor, backgroundColor: `${calStatusColor}20` }}>
            {data.calorie_status.charAt(0).toUpperCase() + data.calorie_status.slice(1)}
          </span>
        </div>
        <div className="mt-2 h-2 overflow-hidden rounded-full bg-bg-elevated">
          <div className="h-full rounded-full transition-all" style={{ width: `${Math.min(data.calorie_percent, 100)}%`, backgroundColor: calStatusColor }} />
        </div>
      </Card>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {macros.map(({ label, value, target, color }) => (
          <Card key={label} padding="md">
            <p className="mb-1 text-xs text-text-muted">{label}</p>
            <p className="text-lg font-bold" style={{ color }}>{value}</p>
            {target && <p className="mt-0.5 text-xs text-text-muted">{target}</p>}
          </Card>
        ))}
      </div>

      <Card>
        <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-text-primary"><Apple size={14} className="text-accent" /> Today's Meals ({data.meal_count})</h3>
        <div className="space-y-2">
          {data.meals_today.map(meal => (
            <div key={meal.id} className="flex items-center justify-between rounded-lg bg-bg-elevated px-3 py-2">
              <div>
                <p className="text-sm text-text-primary">{meal.food_name}</p>
                <p className="text-xs capitalize text-text-muted">{meal.meal_type}{meal.is_pakistani_food ? ' · Pakistani' : ''}</p>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium text-text-primary">{meal.calories} kcal</p>
                <p className="text-xs text-text-muted">{meal.protein_g}g protein</p>
              </div>
            </div>
          ))}
        </div>
      </Card>

      <Card padding="sm">
        <p className="text-center text-xs text-text-muted">Nutritional targets are general population guidelines and do not constitute medical or dietary advice.</p>
      </Card>
    </div>
  )
}
