import { useEffect, useState } from 'react'
import { PageWrapper, Card, Badge, Spinner } from '../components/ui'
import { getDashboard } from '../services/dashboardService'
import { FlaskConical, Apple, Droplets, Cpu, CalendarDays, Activity } from 'lucide-react'

interface TimelineEvent {
  id: string
  date: string
  event_type: string
  title: string
  description: string
  is_ai_generated: boolean
}

const iconMap: Record<string, React.ElementType> = {
  lab: FlaskConical,
  nutrition: Apple,
  hydration: Droplets,
  ai_insight: Cpu,
  plan: CalendarDays,
  activity: Activity,
}

const colorMap: Record<string, string> = {
  lab: 'text-[#0EA5E9] bg-[#0EA5E9]/10 border-[#0EA5E9]/20',
  nutrition: 'text-[#10B981] bg-[#10B981]/10 border-[#10B981]/20',
  hydration: 'text-[#38BDF8] bg-[#38BDF8]/10 border-[#38BDF8]/20',
  ai_insight: 'text-[#A78BFA] bg-[#A78BFA]/10 border-[#A78BFA]/20',
  plan: 'text-[#F59E0B] bg-[#F59E0B]/10 border-[#F59E0B]/20',
  activity: 'text-[#10B981] bg-[#10B981]/10 border-[#10B981]/20',
}

export function HealthTimeline() {
  const [events, setEvents] = useState<TimelineEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    getDashboard()
      .then(d => { setEvents(d.timeline ?? []); setLoading(false) })
      .catch(() => { setError('Could not load timeline. Is the backend running?'); setLoading(false) })
  }, [])

  if (loading) return (
    <PageWrapper title="Health Timeline" subtitle="Your chronological health journey">
      <div className="flex justify-center py-12"><Spinner size="lg" /></div>
    </PageWrapper>
  )

  if (error) return (
    <PageWrapper title="Health Timeline" subtitle="Your chronological health journey">
      <Card><p className="text-[#EF4444] text-sm text-center py-4">{error}</p></Card>
    </PageWrapper>
  )

  return (
    <PageWrapper title="Health Timeline" subtitle="Your chronological health journey">
      <div className="relative">
        <div className="absolute left-5 top-0 bottom-0 w-px bg-[#1F2937]" />
        <div className="space-y-4">
          {events.map(event => {
            const Icon = iconMap[event.event_type] ?? Activity
            const colors = colorMap[event.event_type] ?? colorMap.activity
            return (
              <div key={event.id} className="flex items-start gap-4 pl-10 relative">
                <div className={`absolute left-2 top-3 w-6 h-6 rounded-full border flex items-center justify-center shrink-0 ${colors}`}>
                  <Icon size={12} />
                </div>
                <Card className="flex-1">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-[#F9FAFB] text-sm font-medium">{event.title}</p>
                      <p className="text-[#9CA3AF] text-xs mt-0.5">{event.description}</p>
                    </div>
                    <div className="text-right ml-3 shrink-0">
                      <p className="text-[#6B7280] text-xs">{event.date}</p>
                      {event.is_ai_generated && <Badge label="AI" variant="info" />}
                    </div>
                  </div>
                </Card>
              </div>
            )
          })}
          {events.length === 0 && (
            <Card>
              <p className="text-[#6B7280] text-sm text-center py-4">No timeline events yet.</p>
            </Card>
          )}
        </div>
      </div>
    </PageWrapper>
  )
}
