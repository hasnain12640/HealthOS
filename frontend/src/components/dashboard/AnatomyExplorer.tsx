import { useState } from 'react'
import { Activity, Brain, Droplets, HeartPulse, Salad } from 'lucide-react'
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

  const systems: Record<SystemKey, { label: string; description: string; observations: Array<{ label: string; value: string }> }> = {
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
  }

  const selected = systems[selectedSystem]
  const selectFromKeyboard = (event: React.KeyboardEvent<SVGElement>, system: SystemKey) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      setSelectedSystem(system)
    }
  }
  const regionClass = (system: SystemKey) => [
    'anatomy-region cursor-pointer outline-none transition-all duration-300',
    selectedSystem === system ? 'anatomy-region-active' : 'anatomy-region-idle',
  ].join(' ')

  return (
    <section className="dashboard-glass dashboard-anatomy-panel relative overflow-hidden rounded-3xl border border-primary/20 p-5 sm:p-6">
      <div className="pointer-events-none absolute inset-0 dashboard-grid-overlay opacity-50" />
      <div className="relative flex items-start justify-between gap-4">
        <div>
          <p className="dashboard-eyebrow">{t['dashboard.anatomy_eyebrow']}</p>
          <h2 className="mt-1 text-lg font-semibold text-text-primary">{t['dashboard.anatomy_title']}</h2>
          <p className="mt-1 max-w-md text-xs leading-relaxed text-text-secondary">{t['dashboard.anatomy_disclaimer']}</p>
        </div>
        <span className="rounded-full border border-primary/20 bg-primary/10 px-2.5 py-1 text-[10px] font-medium text-primary">
          {t['dashboard.anatomy_educational']}
        </span>
      </div>

      <div className="relative mt-5 grid gap-5 lg:grid-cols-[minmax(0,1fr)_11rem] lg:items-center">
        <div className="relative mx-auto flex w-full max-w-md items-center justify-center">
          <div className="anatomy-orbit anatomy-orbit-one" />
          <div className="anatomy-orbit anatomy-orbit-two" />
          <svg viewBox="0 0 280 390" className="relative z-10 h-[19rem] w-auto max-w-full sm:h-[22rem]" role="img" aria-label={t['dashboard.anatomy_svg_label']}>
            <title>{t['dashboard.anatomy_svg_label']}</title>
            <path d="M140 25c-25 0-43 19-43 44 0 17 8 31 20 39l-9 34-37 33 15 85 29 13 7 85h36l7-85 29-13 15-85-37-33-9-34c12-8 20-22 20-39 0-25-18-44-43-44Z" className="fill-bg-surface stroke-border-subtle" strokeWidth="2" />
            <path d="M103 154 58 184l17 87 42-12" className="fill-none stroke-border-subtle" strokeWidth="17" strokeLinecap="round" />
            <path d="m177 154 45 30-17 87-42-12" className="fill-none stroke-border-subtle" strokeWidth="17" strokeLinecap="round" />
            <path d="m120 338-18 38M160 338l18 38" className="fill-none stroke-border-subtle" strokeWidth="19" strokeLinecap="round" />

            <g className={regionClass('recovery')} onClick={() => setSelectedSystem('recovery')} onKeyDown={event => selectFromKeyboard(event, 'recovery')} tabIndex={0} role="button" aria-label={systems.recovery.label}>
              <path d="M116 49c7-10 25-15 39-6 9 5 13 15 11 27-8-7-18-7-27-3-9-4-17-2-25 4-2-8-2-15 2-22Z" />
            </g>
            <g className={regionClass('cardiometabolic')} onClick={() => setSelectedSystem('cardiometabolic')} onKeyDown={event => selectFromKeyboard(event, 'cardiometabolic')} tabIndex={0} role="button" aria-label={systems.cardiometabolic.label}>
              <path d="M121 138c-14-16-28-4-20 12l39 42 39-42c8-16-6-28-20-12-8-9-22-9-38 0Z" />
              <path d="M113 118c-16 3-22 20-15 39l26 22v-53c-4-7-7-9-11-8Zm54 0c-5-1-8 1-11 8v53l26-22c7-19 1-36-15-39Z" />
            </g>
            <g className={regionClass('nutrition')} onClick={() => setSelectedSystem('nutrition')} onKeyDown={event => selectFromKeyboard(event, 'nutrition')} tabIndex={0} role="button" aria-label={systems.nutrition.label}>
              <path d="M111 194c11-8 28-6 36 4-1 15-8 26-24 30-13-4-18-17-12-34Zm38 5c11-7 25-3 29 10-5 14-15 21-29 19-5-9-5-19 0-29Z" />
              <path d="M126 232c11-5 22-5 29 0 12 8 8 35-14 38-22-3-27-30-15-38Z" />
            </g>
            <g className={regionClass('hydration')} onClick={() => setSelectedSystem('hydration')} onKeyDown={event => selectFromKeyboard(event, 'hydration')} tabIndex={0} role="button" aria-label={systems.hydration.label}>
              <path d="M141 275c-14 18-17 25-17 33 0 10 7 18 17 18s17-8 17-18c0-8-3-15-17-33Z" />
            </g>
            <g className={regionClass('activity')} onClick={() => setSelectedSystem('activity')} onKeyDown={event => selectFromKeyboard(event, 'activity')} tabIndex={0} role="button" aria-label={systems.activity.label}>
              <path d="m104 182 36 21 36-21M107 290l33 19 33-19M117 349l23 14 23-14" fill="none" strokeWidth="5" strokeLinecap="round" />
            </g>

            <path d="M49 114h43M188 114h43M51 295h64M165 295h64" className="fill-none stroke-primary/40" strokeDasharray="3 5" strokeWidth="1.5" />
            <circle cx="49" cy="114" r="3" className="fill-primary" />
            <circle cx="231" cy="114" r="3" className="fill-primary" />
            <circle cx="51" cy="295" r="3" className="fill-primary" />
            <circle cx="229" cy="295" r="3" className="fill-primary" />
          </svg>
        </div>

        <div className="grid grid-cols-2 gap-2 lg:grid-cols-1">
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
                  'rounded-xl border px-3 py-2 text-start text-xs transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary',
                  isSelected
                    ? 'border-primary/50 bg-primary/15 text-text-primary shadow-[0_0_20px_rgba(14,165,233,0.16)]'
                    : 'border-border bg-bg-base/40 text-text-secondary hover:border-primary/30 hover:text-text-primary',
                ].join(' ')}
              >
                <span className="flex items-center gap-2"><Icon size={14} className="text-primary" />{systems[system].label}</span>
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
    </section>
  )
}
