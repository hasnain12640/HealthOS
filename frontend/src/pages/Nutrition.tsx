import { useEffect, useState } from 'react'
import { PageWrapper, Card, Spinner } from '../components/ui'
import { getAnalysis, type NutritionAnalysis } from '../services/analysisService'
import { Apple, TrendingUp } from 'lucide-react'

export function Nutrition() {
  const [data, setData] = useState<NutritionAnalysis | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    getAnalysis()
      .then(r => setData(r.nutrition))
      .catch(() => setError('Could not load nutrition data. Is the backend running?'))
  }, [])

  if (error) return (
    <PageWrapper title="Nutrition" subtitle="Daily food and nutrition tracking">
      <Card><p className="text-danger text-sm text-center py-4">{error}</p></Card>
    </PageWrapper>
  )

  if (!data) return (
    <PageWrapper title="Nutrition" subtitle="Daily food and nutrition tracking">
      <div className="flex justify-center py-12"><Spinner size="lg" /></div>
    </PageWrapper>
  )

  const macros = [
    { label: 'Calories', value: `${data.total_calories} kcal`, target: `Target: ${data.calorie_target} kcal`, pct: data.calorie_percent, color: 'var(--color-warning)' },
    { label: 'Protein', value: `${data.total_protein_g}g`, target: `Target: ${data.protein_target_g}g`, pct: data.protein_percent, color: 'var(--color-primary)' },
    { label: 'Carbohydrates', value: `${data.total_carbs_g}g`, target: '', pct: null, color: 'var(--color-accent)' },
    { label: 'Fat', value: `${data.total_fat_g}g`, target: '', pct: null, color: 'var(--color-status-high)' },
  ]

  const calStatusColor = data.calorie_status === 'good' ? 'var(--color-status-normal)' : data.calorie_status === 'low' ? 'var(--color-status-low)' : 'var(--color-status-high)'

  return (
    <PageWrapper title="Nutrition" subtitle="Daily food and nutrition tracking">
      <div className="space-y-4">
        {/* Calorie status banner */}
        <Card padding="sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <TrendingUp size={14} style={{ color: calStatusColor }} />
              <span className="text-text-primary text-sm font-medium">
                Calorie intake: {data.calorie_percent}% of target
              </span>
            </div>
            <span className="text-xs px-2 py-0.5 rounded-full" style={{ color: calStatusColor, backgroundColor: `${calStatusColor}20` }}>
              {data.calorie_status.charAt(0).toUpperCase() + data.calorie_status.slice(1)}
            </span>
          </div>
          <div className="mt-2 h-2 bg-bg-elevated rounded-full overflow-hidden">
            <div className="h-full rounded-full transition-all" style={{ width: `${Math.min(data.calorie_percent, 100)}%`, backgroundColor: calStatusColor }} />
          </div>
        </Card>

        {/* Macro summary */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {macros.map(({ label, value, target, color }) => (
            <Card key={label} padding="md">
              <p className="text-text-muted text-xs mb-1">{label}</p>
              <p className="font-bold text-lg" style={{ color }}>{value}</p>
              {target && <p className="text-text-muted text-xs mt-0.5">{target}</p>}
            </Card>
          ))}
        </div>

        {/* Meals */}
        <Card>
          <h3 className="text-text-primary font-semibold text-sm mb-3 flex items-center gap-2">
            <Apple size={14} className="text-accent" /> Today's Meals ({data.meal_count})
          </h3>
          <div className="space-y-2">
            {data.meals_today.map(m => (
              <div key={m.id} className="flex items-center justify-between bg-bg-elevated rounded-lg px-3 py-2">
                <div>
                  <p className="text-text-primary text-sm">{m.food_name}</p>
                  <p className="text-text-muted text-xs capitalize">
                    {m.meal_type}{m.is_pakistani_food ? ' · Pakistani' : ''}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-text-primary text-sm font-medium">{m.calories} kcal</p>
                  <p className="text-text-muted text-xs">{m.protein_g}g protein</p>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card padding="sm">
          <p className="text-text-muted text-xs text-center">
            Nutritional targets are general population guidelines and do not constitute medical or dietary advice.
          </p>
        </Card>
      </div>
    </PageWrapper>
  )
}
