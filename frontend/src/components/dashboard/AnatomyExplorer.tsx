import { useMemo, useState } from 'react'
import { Activity, Brain, Droplets, HeartPulse, Salad, Info } from 'lucide-react'
import { useT } from '../../i18n/useT'
import type { DashboardData } from '../../services/dashboardService'

type SystemKey = 'recovery' | 'cardiometabolic' | 'nutrition' | 'hydration' | 'activity'

interface AnatomyExplorerProps {
  data: DashboardData
}

const systemIcons = {
  recovery: Brain,
  cardiometabolic: HeartPulse,
  nutrition: Salad,
  hydration: Droplets,
  activity: Activity,
}

export function AnatomyExplorer({ data }: AnatomyExplorerProps) {
  const [selectedSystem, setSelectedSystem] = useState<SystemKey>('recovery')
  const t = useT()
  const activitySteps = data.wearable?.steps ?? data.activity.recent.reduce((total, entry) => total + entry.steps, 0)

  const systems: Record<SystemKey, { label: string; description: string; observations: Array<{ label: string; value: string }> }> = useMemo(() => ({
    recovery: {
      label: t['dashboard.anatomy_recovery'],
      description: t['dashboard.anatomy_recovery_desc'],
      observations: [
        { label: t['dashboard.anatomy_sleep'], value: `${data.sleep.avg_hours}h / ${data.sleep.target_hours}h` },
        ...(data.wearable?.resting_heart_rate != null
          ? [{ label: t['wearables.metric_resting_heart_rate'], value: `${data.wearable.resting_heart_rate} bpm` }]
          : []),
      ],
    },
    cardiometabolic: {
      label: t['dashboard.anatomy_cardiometabolic'],
      description: t['dashboard.anatomy_cardiometabolic_desc'],
      observations: [
        {
          label: t['dashboard.anatomy_lab_signals'],
          value: t['dashboard.anatomy_lab_value']
            .replace('{{count}}', String(data.lab_summary.abnormal_count))
            .replace('{{total}}', String(data.lab_summary.total_biomarkers)),
        },
        ...(data.wearable?.steps != null
          ? [{ label: t['wearables.metric_steps'], value: data.wearable.steps.toLocaleString() }]
          : []),
      ],
    },
    nutrition: {
      label: t['dashboard.anatomy_nutrition'],
      description: t['dashboard.anatomy_nutrition_desc'],
      observations: [
        { label: t['dashboard.calories_today'], value: `${data.nutrition.total_calories} kcal` },
        { label: t['dashboard.anatomy_meals'], value: t['dashboard.meals_logged'].replace('{{count}}', String(data.nutrition.meal_count)) },
      ],
    },
    hydration: {
      label: t['dashboard.anatomy_hydration'],
      description: t['dashboard.anatomy_hydration_desc'],
      observations: [
        { label: t['dashboard.hydration_today'], value: `${data.hydration.today_ml} / ${data.hydration.target_ml} ml` },
        { label: t['dashboard.anatomy_progress'], value: `${data.hydration.percent}%` },
      ],
    },
    activity: {
      label: t['dashboard.anatomy_activity'],
      description: t['dashboard.anatomy_activity_desc'],
      observations: [
        {
          label: data.wearable?.steps != null ? t['wearables.metric_steps'] : t['dashboard.anatomy_recent_activity'],
          value: activitySteps > 0 ? activitySteps.toLocaleString() : t['dashboard.anatomy_no_activity'],
        },
        ...(data.wearable?.active_calories != null
          ? [{ label: t['wearables.metric_active_calories'], value: `${data.wearable.active_calories} kcal` }]
          : []),
      ],
    },
  }), [t, data, activitySteps])

  const selected = systems[selectedSystem]

  return (
    <section className="dashboard-glass dashboard-anatomy-panel relative flex flex-col overflow-hidden rounded-3xl border border-primary/20 p-5 sm:p-6">
      <div className="pointer-events-none absolute inset-0 dashboard-grid-overlay opacity-50" />

      <div className="relative grid min-h-0 flex-1 gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,7rem)] lg:items-start">
        <div className="relative flex min-h-[20rem] w-full flex-col sm:min-h-[26rem] lg:min-h-[30rem]">
          <div className="anatomy-stage relative flex flex-1 items-center justify-center overflow-hidden rounded-2xl border border-primary/15 bg-anatomy-stage">
            <img
              src="/assets/anatomy/healthos-anatomy.png"
              alt={t['dashboard.anatomy_svg_label']}
              className="anatomy-image h-full w-full object-contain"
            />
          </div>
        </div>

        <div className="flex flex-row flex-wrap gap-2 lg:flex-col lg:flex-nowrap">
          {(Object.keys(systems) as SystemKey[]).map(system => {
            const Icon = systemIcons[system]
            const isSelected = selectedSystem === system
            return (
              <button
                type="button"
                key={system}
                onClick={() => setSelectedSystem(system)}
                aria-pressed={isSelected}
                className={[
                  'rounded-full border px-3 py-2 text-start text-xs transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary',
                  isSelected
                    ? 'border-primary/50 bg-primary/15 text-text-primary shadow-[0_0_16px_rgba(14,165,233,0.16)]'
                    : 'border-border bg-bg-base/40 text-text-secondary hover:border-primary/30 hover:text-text-primary',
                ].join(' ')}
              >
                <span className="flex items-center gap-2"><Icon size={13} className="text-primary" />{systems[system].label}</span>
              </button>
            )
          })}
        </div>
      </div>

      <div className="relative mt-4 rounded-2xl border border-border bg-bg-base/45 p-4">
        <div className="flex items-center gap-2">
          {(() => {
            const Icon = systemIcons[selectedSystem]
            return <Icon size={15} className="text-primary" />
          })()}
          <h3 className="text-sm font-semibold text-text-primary">{selected.label}</h3>
        </div>
        <p className="mt-1 text-xs leading-relaxed text-text-secondary">{selected.description}</p>
        <div className="mt-3 grid gap-2 sm:grid-cols-2">
          {selected.observations.map(observation => (
            <div key={observation.label} className="rounded-xl bg-bg-elevated/70 px-3 py-2">
              <p className="text-[10px] uppercase tracking-wide text-text-muted">{observation.label}</p>
              <p className="mt-0.5 text-sm font-semibold text-text-primary">{observation.value}</p>
            </div>
          ))}
        </div>
      </div>

      <p className="relative mt-3 flex items-center gap-1.5 text-[10px] text-text-muted">
        <Info size={11} />
        {t['dashboard.anatomy_disclaimer']}
      </p>
    </section>
  )
}
