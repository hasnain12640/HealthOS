import { useEffect, useState } from 'react'
import { Activity, Apple, Droplets, Moon, X } from 'lucide-react'
import { Button, Card } from '../ui'
import {
  logActivity,
  logHydration,
  logNutrition,
  logSleep,
  type NutritionLogInput,
} from '../../services/lifestyleService'
import { useT } from '../../i18n/useT'

export type LifestyleEntryType = 'hydration' | 'nutrition' | 'activity' | 'sleep'

interface ManualLifestyleEntryModalProps {
  open: boolean
  entryType: LifestyleEntryType
  onClose: () => void
  onSuccess: () => void | Promise<void>
}

const today = () => new Date().toISOString().slice(0, 10)

const entryDetails = {
  hydration: { Icon: Droplets, titleKey: 'lifestyle.log_hydration' },
  nutrition: { Icon: Apple, titleKey: 'lifestyle.log_nutrition' },
  activity: { Icon: Activity, titleKey: 'lifestyle.log_activity' },
  sleep: { Icon: Moon, titleKey: 'lifestyle.log_sleep' },
} as const

const mealTypes: NutritionLogInput['meal_type'][] = ['breakfast', 'lunch', 'dinner', 'snack', 'meal', 'other']

function isIntegerInRange(value: string, minimum: number, maximum: number) {
  const number = Number(value)
  return Number.isInteger(number) && number >= minimum && number <= maximum
}

function isNumberInRange(value: string, minimum: number, maximum: number) {
  const number = Number(value)
  return Number.isFinite(number) && number >= minimum && number <= maximum
}

export function ManualLifestyleEntryModal({ open, entryType, onClose, onSuccess }: ManualLifestyleEntryModalProps) {
  const t = useT()
  const [date, setDate] = useState(today)
  const [hydrationAmount, setHydrationAmount] = useState('250')
  const [mealType, setMealType] = useState<NutritionLogInput['meal_type']>('meal')
  const [foodName, setFoodName] = useState('')
  const [quantity, setQuantity] = useState('0')
  const [calories, setCalories] = useState('0')
  const [protein, setProtein] = useState('0')
  const [carbs, setCarbs] = useState('0')
  const [fat, setFat] = useState('0')
  const [isPakistaniFood, setIsPakistaniFood] = useState(true)
  const [hoursSlept, setHoursSlept] = useState('8')
  const [quality, setQuality] = useState('3')
  const [activityType, setActivityType] = useState('')
  const [duration, setDuration] = useState('0')
  const [steps, setSteps] = useState('0')
  const [notes, setNotes] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  useEffect(() => {
    if (!open) return
    setDate(today())
    setHydrationAmount('250')
    setMealType('meal')
    setFoodName('')
    setQuantity('0')
    setCalories('0')
    setProtein('0')
    setCarbs('0')
    setFat('0')
    setIsPakistaniFood(true)
    setHoursSlept('8')
    setQuality('3')
    setActivityType('')
    setDuration('0')
    setSteps('0')
    setNotes('')
    setSaving(false)
    setError(null)
    setSuccess(null)
  }, [open, entryType])

  if (!open) return null

  const details = entryDetails[entryType]
  const Icon = details.Icon

  const getValidationError = () => {
    if (!date || date > today()) return t['lifestyle.date_error']

    if (entryType === 'hydration') {
      return isIntegerInRange(hydrationAmount, 1, 5000) ? null : t['lifestyle.validation_error']
    }
    if (entryType === 'nutrition') {
      return foodName.trim().length > 0
        && isIntegerInRange(quantity, 0, 10000)
        && isIntegerInRange(calories, 0, 10000)
        && isNumberInRange(protein, 0, 1000)
        && isNumberInRange(carbs, 0, 1000)
        && isNumberInRange(fat, 0, 1000)
        ? null
        : t['lifestyle.validation_error']
    }
    if (entryType === 'sleep') {
      return isNumberInRange(hoursSlept, 0.5, 24) && isIntegerInRange(quality, 1, 5)
        ? null
        : t['lifestyle.validation_error']
    }
    return activityType.trim().length > 0
      && isIntegerInRange(duration, 0, 1440)
      && isIntegerInRange(steps, 0, 100000)
      && (Number(duration) > 0 || Number(steps) > 0)
      && notes.length <= 500
      ? null
      : t['lifestyle.validation_error']
  }

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)
    setSuccess(null)

    const validationError = getValidationError()
    if (validationError) {
      setError(validationError)
      return
    }

    setSaving(true)
    try {
      if (entryType === 'hydration') {
        await logHydration({ date, amount_ml: Number(hydrationAmount) })
      } else if (entryType === 'nutrition') {
        await logNutrition({
          date,
          meal_type: mealType,
          food_name: foodName.trim(),
          quantity_g: Number(quantity),
          calories: Number(calories),
          protein_g: Number(protein),
          carbs_g: Number(carbs),
          fat_g: Number(fat),
          is_pakistani_food: isPakistaniFood,
        })
      } else if (entryType === 'sleep') {
        await logSleep({ date, hours_slept: Number(hoursSlept), quality: Number(quality) })
      } else {
        await logActivity({
          date,
          activity_type: activityType.trim(),
          duration_min: Number(duration),
          steps: Number(steps),
          notes: notes.trim(),
        })
      }
      await onSuccess()
      setSuccess(t['lifestyle.entry_saved'])
      window.setTimeout(onClose, 800)
    } catch (requestError: unknown) {
      const detail = (requestError as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(typeof detail === 'string' ? detail : t['lifestyle.save_error'])
    } finally {
      setSaving(false)
    }
  }

  const inputClassName = 'w-full rounded-lg border border-border-subtle bg-bg-elevated px-3 py-2 text-sm text-text-primary outline-none transition-colors focus:border-primary'
  const numberInputClassName = `${inputClassName} [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none`

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center bg-black/60 p-4 backdrop-blur-sm"
      onClick={event => { if (event.target === event.currentTarget && !saving) onClose() }}
    >
      <Card className="mt-8 w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="mb-5 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl border border-primary/20 bg-primary/10 text-primary"><Icon size={17} /></span>
            <h3 className="text-sm font-semibold text-text-primary">{t[details.titleKey]}</h3>
          </div>
          <button type="button" onClick={onClose} disabled={saving} className="text-text-muted transition-colors hover:text-text-primary disabled:cursor-not-allowed disabled:opacity-50" aria-label={t['common.cancel']}>
            <X size={18} />
          </button>
        </div>

        <form className="space-y-4" onSubmit={handleSubmit}>
          <div>
            <label className="mb-1 block text-xs text-text-secondary" htmlFor="lifestyle-date">{t['lifestyle.date']}</label>
            <input id="lifestyle-date" type="date" max={today()} value={date} onChange={event => setDate(event.target.value)} className={inputClassName} />
          </div>

          {entryType === 'hydration' && (
            <div>
              <label className="mb-1 block text-xs text-text-secondary" htmlFor="hydration-amount">{t['lifestyle.amount_ml']}</label>
              <input id="hydration-amount" type="number" min="1" max="5000" step="1" value={hydrationAmount} onChange={event => setHydrationAmount(event.target.value)} className={numberInputClassName} />
            </div>
          )}

          {entryType === 'nutrition' && (
            <>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-xs text-text-secondary" htmlFor="meal-type">{t['lifestyle.meal_type']}</label>
                  <select id="meal-type" value={mealType} onChange={event => setMealType(event.target.value as NutritionLogInput['meal_type'])} className={inputClassName}>
                    {mealTypes.map(type => <option key={type} value={type}>{t[`lifestyle.meal_${type}`]}</option>)}
                  </select>
                </div>
                <div>
                  <label className="mb-1 block text-xs text-text-secondary" htmlFor="food-quantity">{t['lifestyle.quantity_g']}</label>
                  <input id="food-quantity" type="number" min="0" max="10000" step="1" value={quantity} onChange={event => setQuantity(event.target.value)} className={numberInputClassName} />
                </div>
              </div>
              <div>
                <label className="mb-1 block text-xs text-text-secondary" htmlFor="food-name">{t['lifestyle.food_name']}</label>
                <input id="food-name" type="text" maxLength={200} value={foodName} onChange={event => setFoodName(event.target.value)} className={inputClassName} />
              </div>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                <div>
                  <label className="mb-1 block text-xs text-text-secondary" htmlFor="meal-calories">{t['lifestyle.calories']}</label>
                  <input id="meal-calories" type="number" min="0" max="10000" step="1" value={calories} onChange={event => setCalories(event.target.value)} className={numberInputClassName} />
                </div>
                <div>
                  <label className="mb-1 block text-xs text-text-secondary" htmlFor="meal-protein">{t['lifestyle.protein_g']}</label>
                  <input id="meal-protein" type="number" min="0" max="1000" step="0.1" value={protein} onChange={event => setProtein(event.target.value)} className={numberInputClassName} />
                </div>
                <div>
                  <label className="mb-1 block text-xs text-text-secondary" htmlFor="meal-carbs">{t['lifestyle.carbs_g']}</label>
                  <input id="meal-carbs" type="number" min="0" max="1000" step="0.1" value={carbs} onChange={event => setCarbs(event.target.value)} className={numberInputClassName} />
                </div>
                <div>
                  <label className="mb-1 block text-xs text-text-secondary" htmlFor="meal-fat">{t['lifestyle.fat_g']}</label>
                  <input id="meal-fat" type="number" min="0" max="1000" step="0.1" value={fat} onChange={event => setFat(event.target.value)} className={numberInputClassName} />
                </div>
              </div>
              <label className="flex items-center gap-2 text-xs text-text-secondary">
                <input type="checkbox" checked={isPakistaniFood} onChange={event => setIsPakistaniFood(event.target.checked)} className="h-4 w-4 rounded border-border-subtle accent-primary" />
                {t['lifestyle.pakistani_food']}
              </label>
            </>
          )}

          {entryType === 'sleep' && (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-xs text-text-secondary" htmlFor="hours-slept">{t['lifestyle.hours_slept']}</label>
                <input id="hours-slept" type="number" min="0.5" max="24" step="0.5" value={hoursSlept} onChange={event => setHoursSlept(event.target.value)} className={numberInputClassName} />
              </div>
              <div>
                <label className="mb-1 block text-xs text-text-secondary" htmlFor="sleep-quality">{t['lifestyle.sleep_quality']}</label>
                <select id="sleep-quality" value={quality} onChange={event => setQuality(event.target.value)} className={inputClassName}>
                  {[1, 2, 3, 4, 5].map(value => <option key={value} value={value}>{value} / 5</option>)}
                </select>
              </div>
            </div>
          )}

          {entryType === 'activity' && (
            <>
              <div>
                <label className="mb-1 block text-xs text-text-secondary" htmlFor="activity-type">{t['lifestyle.activity_type']}</label>
                <input id="activity-type" type="text" maxLength={100} value={activityType} onChange={event => setActivityType(event.target.value)} className={inputClassName} />
              </div>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-xs text-text-secondary" htmlFor="activity-duration">{t['lifestyle.duration_min']}</label>
                  <input id="activity-duration" type="number" min="0" max="1440" step="1" value={duration} onChange={event => setDuration(event.target.value)} className={numberInputClassName} />
                </div>
                <div>
                  <label className="mb-1 block text-xs text-text-secondary" htmlFor="activity-steps">{t['lifestyle.steps']}</label>
                  <input id="activity-steps" type="number" min="0" max="100000" step="1" value={steps} onChange={event => setSteps(event.target.value)} className={numberInputClassName} />
                </div>
              </div>
              <div>
                <label className="mb-1 block text-xs text-text-secondary" htmlFor="activity-notes">{t['lifestyle.notes']}</label>
                <textarea id="activity-notes" maxLength={500} value={notes} onChange={event => setNotes(event.target.value)} className={`${inputClassName} min-h-20 resize-y`} />
              </div>
            </>
          )}

          {error && <p className="rounded-lg border border-danger/20 bg-danger/10 px-3 py-2 text-xs text-danger">{error}</p>}
          {success && <p className="rounded-lg border border-accent/20 bg-accent/10 px-3 py-2 text-xs text-accent">{success}</p>}

          <div className="flex items-center justify-end gap-2 pt-1">
            <Button type="button" variant="ghost" size="sm" onClick={onClose} disabled={saving}>{t['common.cancel']}</Button>
            <Button type="submit" size="sm" loading={saving}>{t['lifestyle.save_entry']}</Button>
          </div>
        </form>
      </Card>
    </div>
  )
}
