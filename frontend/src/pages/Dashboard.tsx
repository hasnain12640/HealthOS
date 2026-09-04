import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageWrapper, Card, Badge, Spinner } from '../components/ui'
import { getDashboard, type DashboardData } from '../services/dashboardService'
import { getInsight } from '../services/planService'
import { AlertTriangle, Droplets, Moon, FlaskConical, Activity, ChevronRight } from 'lucide-react'

function PriorityCard({ p }: { p: DashboardData['priorities'][0] }) {
  return (
    <Card padding="md">
      <div className="flex items-start justify-between mb-3">
        <h3 className="text-[#F9FAFB] font-medium text-sm pr-2">{p.title}</h3>
        <Badge
          label={p.severity === 'high' ? 'High' : p.severity === 'medium' ? 'Medium' : 'Low'}
          variant={p.severity === 'high' ? 'high' : p.severity === 'medium' ? 'low' : 'normal'}
        />
      </div>
      <div className="space-y-2 text-xs">
        <div className="bg-[#1F2937] rounded-lg p-2.5">
          <p className="text-[#6B7280] uppercase tracking-wide text-[10px] mb-1 font-medium">Observed Data</p>
          <p className="text-[#9CA3AF] leading-relaxed">{p.observed_data}</p>
        </div>
        <div className="bg-[#1F2937] rounded-lg p-2.5">
          <p className="text-[#6B7280] uppercase tracking-wide text-[10px] mb-1 font-medium">AI Interpretation</p>
          <p className="text-[#9CA3AF] leading-relaxed">{p.ai_interpretation}</p>
        </div>
        <div className="bg-[#10B981]/5 border border-[#10B981]/20 rounded-lg p-2.5">
          <p className="text-[#6B7280] uppercase tracking-wide text-[10px] mb-1 font-medium">Suggested Action</p>
          <p className="text-[#9CA3AF] leading-relaxed">{p.suggested_action}</p>
        </div>
      </div>
    </Card>
  )
}

function StatCard({
  icon: Icon, label, value, sub, iconColor = 'text-[#0EA5E9]',
}: {
  icon: React.ElementType
  label: string
  value: string
  sub: string
  iconColor?: string
}) {
  return (
    <Card padding="md">
      <div className="flex items-center gap-2 mb-2">
        <Icon size={14} className={iconColor} />
        <span className="text-[#9CA3AF] text-xs">{label}</span>
      </div>
      <p className="text-[#F9FAFB] text-xl font-bold leading-none mb-1">{value}</p>
      <p className="text-[#9CA3AF] text-xs">{sub}</p>
    </Card>
  )
}

export function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [insightData, setInsightData] = useState<{ text: string; provider: string; date: string } | null>(null)
  const navigate = useNavigate()

  useEffect(() => {
    getDashboard()
      .then(d => {
        setData(d)
        // Fetch live AI insight — fall back to dashboard's static text if it fails
        getInsight()
          .then(setInsightData)
          .catch(() => setInsightData({
            text: d.ai_insight.text,
            provider: d.ai_insight.generated_by,
            date: d.ai_insight.date,
          }))
      })
      .catch(() => setError('Could not connect to the HealthOS backend. Make sure start-backend.bat is running.'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner size="lg" label="Loading your health data…" />
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3">
        <div className="w-12 h-12 rounded-full bg-[#EF4444]/10 border border-[#EF4444]/20 flex items-center justify-center">
          <AlertTriangle size={20} className="text-[#EF4444]" />
        </div>
        <p className="text-[#F9FAFB] font-medium text-sm">Backend not reachable</p>
        <p className="text-[#9CA3AF] text-xs text-center max-w-sm">{error}</p>
        <button
          onClick={() => { setLoading(true); setError(null); getDashboard().then(setData).catch(e => setError(e.message)).finally(() => setLoading(false)) }}
          className="text-[#0EA5E9] text-xs underline hover:no-underline"
        >
          Retry
        </button>
      </div>
    )
  }

  const { profile, lab_summary, hydration, nutrition, sleep, priorities, ai_insight } = data
  const firstName = profile.user_name.split(' ')[0]
  const hour = new Date().getHours()
  const greeting = hour >= 5 && hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening'
  const hydPct = hydration.percent
  const hydColor = hydPct >= 80 ? '#10B981' : hydPct >= 50 ? '#F59E0B' : '#EF4444'

  return (
    <PageWrapper
      title={`${greeting}, ${firstName}`}
      subtitle={`${profile.city} · ${profile.bmi_category} (BMI ${profile.bmi})`}
    >
      <div className="space-y-6">

        {/* Quick stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <StatCard
            icon={FlaskConical} label="Abnormal Results"
            value={String(lab_summary.abnormal_count)}
            sub={`of ${lab_summary.total_biomarkers} biomarkers`}
            iconColor="text-[#0EA5E9]"
          />
          <StatCard
            icon={Droplets} label="Hydration Today"
            value={`${hydPct}%`}
            sub={`${hydration.today_ml} ml of ${hydration.target_ml} ml`}
            iconColor="text-[#38BDF8]"
          />
          <StatCard
            icon={Moon} label="Avg Sleep"
            value={`${sleep.avg_hours}h`}
            sub="7-day average"
            iconColor={sleep.avg_hours >= 7 ? 'text-[#10B981]' : 'text-[#F59E0B]'}
          />
          <StatCard
            icon={Activity} label="Calories Today"
            value={`${nutrition.total_calories}`}
            sub={`${nutrition.meal_count} meals logged`}
            iconColor="text-[#10B981]"
          />
        </div>

        {/* Health Priorities */}
        <section>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <AlertTriangle size={15} className="text-[#F59E0B]" />
              <h2 className="text-[#F9FAFB] font-semibold text-sm">Health Priorities</h2>
              <span className="text-[#6B7280] text-xs">— {priorities.length} identified</span>
            </div>
            <button
              onClick={() => navigate('/lab-reports/report-001')}
              className="flex items-center gap-1 text-[#0EA5E9] text-xs hover:underline"
            >
              View lab detail <ChevronRight size={12} />
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {priorities.map(p => <PriorityCard key={p.id} p={p} />)}
          </div>
        </section>

        {/* Hydration bar */}
        <Card>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Droplets size={14} className="text-[#38BDF8]" />
              <h2 className="text-[#F9FAFB] font-semibold text-sm">Hydration Today</h2>
            </div>
            <span className="font-bold text-sm" style={{ color: hydColor }}>{hydPct}%</span>
          </div>
          <div className="h-2.5 bg-[#1F2937] rounded-full overflow-hidden mb-2">
            <div
              className="h-full rounded-full transition-all duration-700"
              style={{ width: `${Math.min(hydPct, 100)}%`, backgroundColor: hydColor }}
            />
          </div>
          <p className="text-[#9CA3AF] text-xs">
            {hydration.today_ml} ml consumed — {hydration.target_ml - hydration.today_ml > 0
              ? `${hydration.target_ml - hydration.today_ml} ml remaining`
              : 'Daily target reached!'}
          </p>
        </Card>

        {/* Sleep mini-chart */}
        <Card>
          <div className="flex items-center gap-2 mb-3">
            <Moon size={14} className="text-[#A78BFA]" />
            <h2 className="text-[#F9FAFB] font-semibold text-sm">Sleep — Last 7 Nights</h2>
            <span className={`text-xs font-medium ${sleep.avg_hours >= 7 ? 'text-[#10B981]' : 'text-[#F59E0B]'}`}>
              avg {sleep.avg_hours}h
            </span>
          </div>
          <div className="flex items-end gap-1.5 h-14">
            {sleep.logs.map((s, i) => {
              const pct = Math.round((s.hours_slept / 9) * 100)
              const color = s.hours_slept >= 7 ? '#10B981' : s.hours_slept >= 6 ? '#F59E0B' : '#EF4444'
              return (
                <div key={i} className="flex-1 flex flex-col items-center gap-1">
                  <div
                    className="w-full rounded-t"
                    style={{ height: `${pct}%`, backgroundColor: color, minHeight: '4px' }}
                    title={`${s.date}: ${s.hours_slept}h`}
                  />
                  <span className="text-[#6B7280] text-[9px]">{s.hours_slept}h</span>
                </div>
              )
            })}
          </div>
        </Card>

        {/* AI Insight */}
        <Card>
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-[#0EA5E9]/10 border border-[#0EA5E9]/20 flex items-center justify-center shrink-0 mt-0.5">
              <span className="text-[#0EA5E9] text-xs font-bold">AI</span>
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <p className="text-[#6B7280] text-xs">
                  Latest AI Insight · {insightData?.date ?? ai_insight.date}
                </p>
                {insightData && (
                  <span className={[
                    'text-[10px] font-medium px-1.5 py-0.5 rounded-full border',
                    insightData.provider === 'qwen'
                      ? 'text-[#10B981] bg-[#10B981]/10 border-[#10B981]/20'
                      : 'text-[#6B7280] bg-[#374151] border-[#4B5563]',
                  ].join(' ')}>
                    {insightData.provider === 'qwen' ? 'Qwen' : 'Mock'}
                  </span>
                )}
              </div>
              <p className="text-[#F9FAFB] text-sm leading-relaxed">
                {insightData?.text ?? ai_insight.text}
              </p>
              <p className="text-[#6B7280] text-xs mt-2 italic">
                AI responses are for educational purposes only. Not a substitute for professional medical advice.
              </p>
            </div>
          </div>
        </Card>

        {/* Latest lab summary */}
        {lab_summary.report_id && (
          <Card padding="none">
            <div className="flex items-center justify-between px-5 py-4 border-b border-[#1F2937]">
              <div className="flex items-center gap-2">
                <FlaskConical size={14} className="text-[#0EA5E9]" />
                <h2 className="text-[#F9FAFB] font-semibold text-sm">Latest Lab Report</h2>
              </div>
              <button
                onClick={() => navigate(`/lab-reports/${lab_summary.report_id}`)}
                className="flex items-center gap-1 text-[#0EA5E9] text-xs hover:underline"
              >
                Full detail <ChevronRight size={12} />
              </button>
            </div>
            <div className="p-4 grid grid-cols-2 sm:grid-cols-4 gap-2">
              {lab_summary.biomarkers.slice(0, 4).map(b => (
                <div key={b.id} className="bg-[#1F2937] rounded-lg p-2.5">
                  <p className="text-[#6B7280] text-[10px] mb-1 truncate">{b.name}</p>
                  <p className="text-[#F9FAFB] font-semibold text-sm">
                    {b.value} <span className="text-[#6B7280] text-[10px] font-normal">{b.unit}</span>
                  </p>
                  <Badge
                    label={b.status.charAt(0).toUpperCase() + b.status.slice(1)}
                    variant={b.status as 'normal' | 'low' | 'high' | 'critical'}
                    size="sm"
                  />
                </div>
              ))}
            </div>
          </Card>
        )}

      </div>
    </PageWrapper>
  )
}
