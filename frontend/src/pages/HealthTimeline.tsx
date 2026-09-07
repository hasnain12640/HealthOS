import { useEffect, useState } from 'react'
import { PageWrapper, Card, Badge, Spinner } from '../components/ui'
import { getDashboard } from '../services/dashboardService'
import { FlaskConical, Apple, Droplets, Cpu, CalendarDays, Activity, Watch, Heart, Moon, Stethoscope } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

interface TimelineEvent {
  id: string
  date: string
  event_type: string
  title: string
  description: string
  is_ai_generated: boolean
}

const iconMap: Record<string, LucideIcon> = {
  lab: FlaskConical,
  nutrition: Apple,
  hydration: Droplets,
  ai_insight: Cpu,
  plan: CalendarDays,
  activity: Activity,
  sleep: Moon,
  wearable: Watch,
  cycle: Heart,
  cycle_symptom: Stethoscope,
}

const colorMap: Record<string, string> = {
  lab: 'text-primary bg-primary/10 border-primary/20',
  nutrition: 'text-accent bg-accent/10 border-accent/20',
  hydration: 'text-primary-light bg-primary-light/10 border-primary-light/20',
  ai_insight: 'text-primary-light bg-primary-light/10 border-primary-light/20',
  plan: 'text-warning bg-warning/10 border-warning/20',
  activity: 'text-accent bg-accent/10 border-accent/20',
  sleep: 'text-primary-light bg-primary-light/10 border-primary-light/20',
  wearable: 'text-primary bg-primary/10 border-primary/20',
  cycle: 'text-status-high bg-status-high/10 border-status-high/20',
  cycle_symptom: 'text-status-low bg-status-low/10 border-status-low/20',
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
      <Card><p className="text-danger text-sm text-center py-4">{error}</p></Card>
    </PageWrapper>
  )

  return (
    <PageWrapper title="Health Timeline" subtitle="Your chronological health journey">
      <div className="relative">
        <div className="absolute start-5 top-0 bottom-0 w-px bg-border-subtle" />
        <div className="space-y-4">
          {events.map(event => {
            const Icon = iconMap[event.event_type] ?? Activity
            const colors = colorMap[event.event_type] ?? colorMap.activity
            return (
              <div key={event.id} className="flex items-start gap-4 ps-10 relative">
                <div className={`absolute start-2 top-3 w-6 h-6 rounded-full border flex items-center justify-center shrink-0 ${colors}`}>
                  <Icon size={12} />
                </div>
                <Card className="flex-1">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-text-primary text-sm font-medium">{event.title}</p>
                      <p className="text-text-secondary text-xs mt-0.5">{event.description}</p>
                    </div>
                    <div className="text-end ms-3 shrink-0">
                      <p className="text-text-muted text-xs">{event.date}</p>
                      {event.is_ai_generated && <Badge label="AI" variant="info" />}
                    </div>
                  </div>
                </Card>
              </div>
            )
          })}
          {events.length === 0 && (
            <Card>
              <p className="text-text-muted text-sm text-center py-4">No timeline events yet.</p>
            </Card>
          )}
        </div>
      </div>
    </PageWrapper>
  )
}
