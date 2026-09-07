import { Bot, Link2, MessageCircle, ShieldAlert, Sparkles } from 'lucide-react'
import { Badge } from '../ui'
import { VoiceAgentTrigger } from '../voice/VoiceAgentTrigger'
import { useT } from '../../i18n/useT'
import type { InsightData } from '../../services/planService'
import type { DashboardData } from '../../services/dashboardService'
import type { InsightDomain } from '../../types'

interface DashboardInsightProps {
  insightData: InsightData | null
  fallbackInsight: DashboardData['ai_insight']
  onAskAI: () => void
  userSex?: 'male' | 'female'
}

const domainBadgeStyles: Record<InsightDomain, string> = {
  labs: 'text-primary bg-primary/10 border-primary/20',
  hydration: 'text-primary-light bg-primary-light/10 border-primary-light/20',
  sleep: 'text-fertile bg-fertile/10 border-fertile/20',
  activity: 'text-accent bg-accent/10 border-accent/20',
  nutrition: 'text-warning bg-warning/10 border-warning/20',
  wearable: 'text-status-normal bg-status-normal/10 border-status-normal/20',
  cycle: 'text-cycle-light bg-cycle/10 border-cycle/20',
}

function DomainBadge({ domain, label }: { domain: InsightDomain; label: string }) {
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-medium ${domainBadgeStyles[domain]}`}>
      {label}
    </span>
  )
}

export function DashboardInsight({ insightData, fallbackInsight, onAskAI, userSex }: DashboardInsightProps) {
  const t = useT()
  const showCycleContent = userSex === 'female'
  const domainLabel: Record<InsightDomain, string> = {
    labs: t['insight.domain_labs'],
    hydration: t['insight.domain_hydration'],
    sleep: t['insight.domain_sleep'],
    activity: t['insight.domain_activity'],
    nutrition: t['insight.domain_nutrition'],
    wearable: t['insight.domain_wearable'],
    cycle: t['insight.domain_cycle'],
  }

  const observedData = insightData?.insight
    ? insightData.insight.observed_data.filter(item => showCycleContent || item.domain !== 'cycle')
    : []
  const crossDomainConnections = insightData?.insight
    ? insightData.insight.cross_domain_connections.filter(connection =>
        showCycleContent || !connection.domains.includes('cycle'))
    : []
  const priorities = insightData?.insight
    ? insightData.insight.priorities.filter(priority =>
        showCycleContent || !priority.related_domains.includes('cycle'))
    : []

  const hasContent = insightData?.insight || insightData?.text || fallbackInsight.text

  return (
    <section className="dashboard-glass overflow-hidden rounded-3xl border border-primary/25 p-5 sm:p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex min-w-0 items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-primary/30 bg-primary/10 shadow-[0_0_24px_rgba(14,165,233,0.2)]">
            <Bot size={18} className="text-primary" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-text-primary">{t['dashboard.ai_intelligence']}</h2>
            <p className="text-xs text-text-secondary">{t['dashboard.ai_health_intelligence_subtitle']}</p>
          </div>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <button
            type="button"
            onClick={onAskAI}
            className="inline-flex items-center justify-center gap-2 rounded-lg border border-border-subtle bg-bg-base/50 px-3 py-2 text-sm font-medium text-text-primary transition-colors hover:border-primary/40 hover:text-primary"
          >
            <MessageCircle size={15} />
            {t['dashboard.ask_ai']}
          </button>
          <button
            type="button"
            onClick={onAskAI}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white shadow-[0_0_22px_rgba(14,165,233,0.25)] transition-colors hover:bg-primary-dark"
          >
            <Sparkles size={15} />
            {t['dashboard.ask_healthos']}
          </button>
          <VoiceAgentTrigger label={t['dashboard.ask_mira']} className="border-primary/50 bg-primary text-white shadow-[0_0_22px_rgba(14,165,233,0.25)] hover:bg-primary-dark hover:text-white" />
        </div>
      </div>

      {hasContent ? (
        <div className="mt-5 space-y-5">
          {insightData?.insight && (
            <>
              <div className="max-w-3xl">
                <h3 className="text-base font-bold leading-snug text-text-primary">{insightData.insight.headline}</h3>
                <p className="mt-2 text-sm leading-relaxed text-text-secondary">{insightData.insight.summary}</p>
              </div>

              {observedData.length > 0 && (
                <div>
                  <p className="dashboard-section-label">{t['dashboard.observed_data']}</p>
                  <div className="mt-2 grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
                    {observedData.map((observation, index) => (
                      <div key={`${observation.domain}-${index}`} className="rounded-xl border border-border bg-bg-base/45 p-3">
                        <div className="flex items-start justify-between gap-2">
                          <p className="text-xs leading-snug text-text-secondary">{observation.observation}</p>
                          <DomainBadge domain={observation.domain} label={domainLabel[observation.domain] ?? observation.domain} />
                        </div>
                        <p className="mt-1 text-sm font-semibold text-text-primary">{observation.value}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {crossDomainConnections.length > 0 && (
                <div>
                  <p className="dashboard-section-label flex items-center gap-1.5"><Link2 size={12} />{t['insight.cross_domain_connections']}</p>
                  <div className="mt-2 grid gap-2 xl:grid-cols-2">
                    {crossDomainConnections.map((connection, index) => (
                      <div key={index} className="rounded-xl border border-border bg-bg-base/45 p-3">
                        <div className="flex flex-wrap items-center gap-1.5">
                          {connection.domains.map((domain, domainIndex) => (
                            <span key={`${domain}-${domainIndex}`} className="flex items-center gap-1.5">
                              {domainIndex > 0 && <Link2 size={10} className="text-text-muted" />}
                              <DomainBadge domain={domain} label={domainLabel[domain] ?? domain} />
                            </span>
                          ))}
                        </div>
                        <p className="mt-2 text-xs font-semibold text-text-primary">{connection.relationship}</p>
                        <p className="mt-1 text-xs leading-relaxed text-text-secondary">{connection.explanation}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {priorities.length > 0 && (
                <div>
                  <p className="dashboard-section-label">{t['insight.ai_priorities']}</p>
                  <div className="mt-2 grid gap-2 xl:grid-cols-2">
                    {priorities.map((priority, index) => (
                      <div key={index} className="rounded-xl border border-border bg-bg-base/45 p-3">
                        <div className="flex items-start justify-between gap-2">
                          <p className="text-xs font-semibold text-text-primary">{priority.title}</p>
                          <Badge
                            label={
                              priority.urgency === 'high' ? t['insight.urgency_high']
                                : priority.urgency === 'medium' ? t['insight.urgency_medium']
                                : t['insight.urgency_low']
                            }
                            variant={priority.urgency === 'high' ? 'high' : priority.urgency === 'medium' ? 'low' : 'normal'}
                          />
                        </div>
                        <p className="mt-1.5 text-xs leading-relaxed text-text-secondary">{priority.rationale}</p>
                        <p className="mt-2 rounded-lg border border-accent/20 bg-accent/5 px-2.5 py-2 text-xs leading-relaxed text-text-secondary">{priority.suggested_action}</p>
                        {priority.related_domains.length > 0 && (
                          <div className="mt-2 flex flex-wrap gap-1.5">
                            {priority.related_domains.map((domain, domainIndex) => (
                              <DomainBadge key={`${domain}-${domainIndex}`} domain={domain} label={domainLabel[domain] ?? domain} />
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {!insightData?.insight && (insightData?.text || fallbackInsight.text) && (
            <p className="text-sm leading-relaxed text-text-primary">{insightData?.text ?? fallbackInsight.text}</p>
          )}

          <p className="flex items-start gap-1.5 text-xs italic text-text-muted">
            <ShieldAlert size={13} className="mt-0.5 shrink-0" />
            {insightData?.insight?.safety_note ?? t['dashboard.ai_disclaimer']}
          </p>
        </div>
      ) : (
        <p className="mt-5 text-xs text-text-muted">{t['insight.generating']}</p>
      )}
    </section>
  )
}
