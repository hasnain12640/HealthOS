import { useState } from 'react'
import { PageWrapper, Card, Badge, Button, Spinner } from '../components/ui'
import { CalendarDays, CheckCircle2, Sparkles, RefreshCw } from 'lucide-react'
import { generatePlan } from '../services/planService'
import type { DayPlan } from '../types'

function ProviderBadge({ provider }: { provider: string }) {
  const isQwen = provider === 'qwen'
  return (
    <span className={[
      'text-[10px] font-medium px-2 py-0.5 rounded-full border',
      isQwen
        ? 'text-[#10B981] bg-[#10B981]/10 border-[#10B981]/20'
        : 'text-[#6B7280] bg-[#374151] border-[#4B5563]',
    ].join(' ')}>
      {isQwen ? 'Qwen' : 'Mock'}
    </span>
  )
}

function DayCard({ day }: { day: DayPlan }) {
  return (
    <Card padding="md">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-full bg-[#0EA5E9] flex items-center justify-center shrink-0">
            <span className="text-white text-xs font-bold">{day.day}</span>
          </div>
          <p className="text-[#F9FAFB] font-medium text-sm">{day.dayLabel}</p>
        </div>
        <Badge label={day.focus} variant="info" />
      </div>

      <div className="space-y-2 text-xs">
        <div className="bg-[#1F2937] rounded-lg p-2">
          <p className="text-[#6B7280] uppercase tracking-wide text-[10px] mb-1.5 flex items-center gap-1">
            <CalendarDays size={10} /> Nutrition
          </p>
          <ul className="space-y-1">
            {day.nutrition.map((tip, i) => (
              <li key={i} className="flex items-start gap-1.5 text-[#9CA3AF]">
                <CheckCircle2 size={10} className="text-[#10B981] mt-0.5 shrink-0" />
                {tip}
              </li>
            ))}
          </ul>
        </div>
        {[
          { label: 'Hydration', value: day.hydration },
          { label: 'Activity', value: day.activity },
          { label: 'Sleep', value: day.sleep },
        ].map(({ label, value }) => (
          <div key={label} className="bg-[#1F2937] rounded-lg p-2">
            <p className="text-[#6B7280] uppercase tracking-wide text-[10px] mb-1">{label}</p>
            <p className="text-[#9CA3AF]">{value}</p>
          </div>
        ))}
      </div>
    </Card>
  )
}

export function SevenDayPlan() {
  const [plan, setPlan] = useState<{ summary: string; days: DayPlan[] } | null>(null)
  const [provider, setProvider] = useState('')
  const [generatedAt, setGeneratedAt] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleGenerate = async () => {
    setLoading(true)
    setError('')
    try {
      const result = await generatePlan()
      // Backend returns snake_case day_label — map to camelCase DayPlan type
      const days: DayPlan[] = result.plan.days.map((d: any) => ({
        day: d.day,
        dayLabel: d.day_label ?? d.dayLabel,
        focus: d.focus,
        nutrition: d.nutrition,
        hydration: d.hydration,
        activity: d.activity,
        sleep: d.sleep,
      }))
      setPlan({ summary: result.plan.summary, days })
      setProvider(result.provider)
      setGeneratedAt(result.generated_at)
    } catch {
      setError('Could not generate plan. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  return (
    <PageWrapper title="7-Day Action Plan" subtitle="Personalized plan based on your lab results and lifestyle data">
      <div className="space-y-4">

        {/* Pre-generation state */}
        {!plan && !loading && (
          <Card>
            <div className="flex flex-col items-center text-center py-6 gap-4">
              <div className="w-12 h-12 rounded-xl bg-[#0EA5E9]/10 border border-[#0EA5E9]/20 flex items-center justify-center">
                <Sparkles size={20} className="text-[#0EA5E9]" />
              </div>
              <div>
                <p className="text-[#F9FAFB] font-semibold mb-1">Generate Your 7-Day Wellness Plan</p>
                <p className="text-[#9CA3AF] text-sm max-w-md">
                  Your plan is personalised based on your lab results, hydration, sleep, and activity data — with Pakistani food and lifestyle context.
                </p>
              </div>
              {error && <p className="text-[#EF4444] text-sm">{error}</p>}
              <Button onClick={handleGenerate}>
                <Sparkles size={14} /> Generate My Plan
              </Button>
              <p className="text-[#6B7280] text-xs italic">
                This plan provides general wellness guidance and does not substitute professional medical advice.
              </p>
            </div>
          </Card>
        )}

        {/* Loading state */}
        {loading && (
          <Card>
            <div className="flex flex-col items-center py-10 gap-3">
              <Spinner size="lg" />
              <p className="text-[#9CA3AF] text-sm">Generating your personalised plan…</p>
            </div>
          </Card>
        )}

        {/* Generated plan */}
        {plan && !loading && (
          <>
            {/* Summary card */}
            <Card>
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-lg bg-[#0EA5E9]/10 border border-[#0EA5E9]/20 flex items-center justify-center shrink-0">
                  <span className="text-[#0EA5E9] text-xs font-bold">AI</span>
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <p className="text-[#6B7280] text-xs">Generated by HealthOS AI · {generatedAt}</p>
                    <ProviderBadge provider={provider} />
                  </div>
                  <p className="text-[#F9FAFB] text-sm leading-relaxed">{plan.summary}</p>
                  <p className="text-[#6B7280] text-xs mt-2 italic">
                    This plan provides general wellness guidance and does not substitute professional medical advice.
                  </p>
                </div>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={handleGenerate}
                  disabled={loading}
                >
                  <RefreshCw size={12} /> Regenerate
                </Button>
              </div>
            </Card>

            {/* Day cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {plan.days.map(day => (
                <DayCard key={day.day} day={day} />
              ))}
            </div>
          </>
        )}
      </div>
    </PageWrapper>
  )
}
