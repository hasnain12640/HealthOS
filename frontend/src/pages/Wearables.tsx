import { useEffect, useState, useCallback } from 'react'
import { PageWrapper, Card, Badge, Button, Spinner } from '../components/ui'
import { useT } from '../i18n/useT'
import {
  getWearableStatus,
  demoConnect,
  syncDevice,
  disconnectDevice,
  getWeeklySteps,
  getSyncHistory,
  type WearableStatusData,
  type WearableWeeklyDay,
  type WearableSyncHistoryItem,
} from '../services/wearableService'
import {
  Watch, RefreshCw, Unlink, Bluetooth, Heart, Footprints,
  Flame, Moon, MapPin, Droplets, Weight, Brain, Clock,
  CheckCircle2, XCircle, AlertTriangle, Zap,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid,
} from 'recharts'

const metricIcons: Record<string, LucideIcon> = {
  steps: Footprints,
  active_calories: Flame,
  resting_heart_rate: Heart,
  avg_heart_rate: Heart,
  sleep: Moon,
  sleep_score: Brain,
  distance: MapPin,
  water: Droplets,
  weight: Weight,
}

const metricColors: Record<string, string> = {
  steps: 'text-primary',
  active_calories: 'text-[#F59E0B]',
  resting_heart_rate: 'text-[#EF4444]',
  avg_heart_rate: 'text-[#EC4899]',
  sleep: 'text-[#A78BFA]',
  distance: 'text-accent',
  water: 'text-primary-light',
  weight: 'text-text-secondary',
}

function formatMetricValue(metricType: string, value: number, unit: string): { text: string; hasInlineUnit: boolean } {
  if (metricType === 'steps') return { text: value.toLocaleString(), hasInlineUnit: true }
  if (metricType === 'distance') return { text: `${value} ${unit}`, hasInlineUnit: true }
  if (metricType === 'sleep') {
    const h = Math.floor(value)
    const m = Math.round((value - h) * 60)
    return { text: `${h}h ${m}m`, hasInlineUnit: true }
  }
  if (metricType === 'sleep_score') return { text: String(Math.round(value)), hasInlineUnit: true }
  if (metricType === 'water') return { text: `${value} ${unit}`, hasInlineUnit: true }
  if (metricType === 'weight') return { text: `${value} ${unit}`, hasInlineUnit: true }
  return { text: unit ? `${Math.round(value)} ${unit}` : String(Math.round(value)), hasInlineUnit: true }
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

export function Wearables() {
  const t = useT()
  const [status, setStatus] = useState<WearableStatusData | null>(null)
  const [weekly, setWeekly] = useState<WearableWeeklyDay[]>([])
  const [syncs, setSyncs] = useState<WearableSyncHistoryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [connecting, setConnecting] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [disconnecting, setDisconnecting] = useState(false)

  const fetchData = useCallback(async () => {
    const st = await getWearableStatus()
    setStatus(st)
    if (st.device) {
      const [w, h] = await Promise.all([
        getWeeklySteps(st.device.connection_id),
        getSyncHistory(st.device.connection_id),
      ])
      setWeekly(w)
      setSyncs(h)
    } else {
      setWeekly([])
      setSyncs([])
    }
  }, [])

  useEffect(() => {
    fetchData()
      .catch(() => setError(t['common.backend_not_reachable']))
      .finally(() => setLoading(false))
  }, [fetchData, t])

  const handleConnect = async () => {
    setConnecting(true)
    try {
      await demoConnect()
      await fetchData()
    } catch {
      setError(t['common.backend_not_reachable'])
    } finally {
      setConnecting(false)
    }
  }

  const handleSync = async () => {
    if (!status?.device) return
    setSyncing(true)
    try {
      await syncDevice(status.device.connection_id)
      await fetchData()
    } catch {
      setError(t['common.backend_not_reachable'])
    } finally {
      setSyncing(false)
    }
  }

  const handleDisconnect = async () => {
    if (!status?.device) return
    setDisconnecting(true)
    try {
      await disconnectDevice(status.device.connection_id)
      await fetchData()
    } catch {
      setError(t['common.backend_not_reachable'])
    } finally {
      setDisconnecting(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner size="lg" label={t['common.loading_health_data']} />
      </div>
    )
  }

  if (error && !status) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3">
        <div className="w-12 h-12 rounded-full bg-danger/10 border border-danger/20 flex items-center justify-center">
          <AlertTriangle size={20} className="text-danger" />
        </div>
        <p className="text-text-primary font-medium text-sm">{t['common.backend_not_reachable']}</p>
        <button
          onClick={() => { setLoading(true); setError(null); fetchData().catch(() => setError(t['common.backend_not_reachable'])).finally(() => setLoading(false)) }}
          className="text-primary text-xs underline hover:no-underline"
        >
          {t['common.retry']}
        </button>
      </div>
    )
  }

  const connected = status?.connected ?? false
  const device = status?.device
  const insight = status?.insight

  const sleepScoreNum = (() => {
    if (!device?.sleep_score) return null
    const match = device.sleep_score.match(/\d+/)
    return match ? Number(match[0]) : null
  })()

  const metricsDisplay = device
    ? [
        { type: 'steps', value: device.steps, unit: '', target: 10000 },
        { type: 'active_calories', value: device.active_calories, unit: 'kcal', target: 500 },
        { type: 'resting_heart_rate', value: device.resting_heart_rate, unit: 'bpm' },
        { type: 'avg_heart_rate', value: null, unit: 'bpm' },
        { type: 'sleep', value: device.sleep_hours, unit: 'h', target: 7 },
        { type: 'sleep_score', value: sleepScoreNum, unit: '' },
        { type: 'distance', value: device.distance_km, unit: 'km', target: 8 },
        { type: 'water', value: device.hydration_liters, unit: 'L', target: 2.5 },
        { type: 'weight', value: null, unit: 'kg' },
      ].filter(m => m.value != null)
    : []

  return (
    <PageWrapper title={t['wearables.title']} subtitle={t['wearables.subtitle']}>
      <div className="space-y-6">

        {/* Device Card */}
        <Card>
          {connected && device ? (
            <div className="flex flex-col sm:flex-row sm:items-center gap-4">
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <div className="w-12 h-12 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center shrink-0">
                  <Watch size={22} className="text-primary" />
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="text-text-primary font-semibold text-sm">{device.device_name}</h3>
                    <Badge label="Connected" variant="normal" size="sm" />
                  </div>
                  <p className="text-text-secondary text-xs mt-0.5">
                    {device.device_type} · {device.provider.replace('_mock', '')}
                  </p>
                  <p className="text-text-muted text-xs mt-0.5">
                    {t['wearables.last_synced']} {timeAgo(device.last_synced_at)}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleSync}
                  loading={syncing}
                  disabled={disconnecting}
                >
                  <RefreshCw size={14} />
                  {syncing ? t['wearables.syncing'] : t['wearables.sync_now']}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleDisconnect}
                  loading={disconnecting}
                  disabled={syncing}
                >
                  <Unlink size={14} />
                  {disconnecting ? t['wearables.disconnecting'] : t['wearables.disconnect']}
                </Button>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center text-center py-6">
              <div className="w-14 h-14 rounded-full bg-bg-elevated border border-border-subtle flex items-center justify-center mb-3">
                <Bluetooth size={24} className="text-text-muted" />
              </div>
              <h3 className="text-text-primary font-medium text-sm mb-1">{t['wearables.no_device']}</h3>
              <p className="text-text-secondary text-xs mb-4 max-w-sm">{t['wearables.no_device_desc']}</p>
              <Button onClick={handleConnect} loading={connecting} size="sm">
                <Zap size={14} />
                {connecting ? t['wearables.connecting'] : t['wearables.connect_demo']}
              </Button>
            </div>
          )}
        </Card>

        {/* Today's Health Signals */}
        {connected && metricsDisplay.length > 0 && (
          <section>
            <h2 className="text-text-primary font-semibold text-sm mb-3">{t['wearables.todays_signals']}</h2>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              {metricsDisplay.map(m => {
                const Icon = metricIcons[m.type] ?? Zap
                const color = metricColors[m.type] ?? 'text-primary'
                const label = t[`wearables.metric_${m.type}` as keyof typeof t] ?? m.type
                const formatted = formatMetricValue(m.type, m.value!, m.unit)
                let pct: number | null = null
                if (m.target && m.value != null) {
                  pct = Math.min(Math.round((m.value / m.target) * 100), 100)
                }
                return (
                  <Card key={m.type} padding="md">
                    <div className="flex items-center gap-2 mb-2">
                      <Icon size={14} className={color} />
                      <span className="text-text-secondary text-xs">{label}</span>
                    </div>
                    <p className="text-text-primary text-xl font-bold leading-none mb-1">
                      {formatted.text}
                    </p>
                    {pct != null ? (
                      <div className="mt-2">
                        <div className="h-1.5 bg-bg-elevated rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full transition-all duration-500"
                            style={{
                              width: `${pct}%`,
                              backgroundColor: pct >= 80 ? '#10B981' : pct >= 50 ? '#F59E0B' : '#EF4444',
                            }}
                          />
                        </div>
                        <p className="text-text-muted text-[10px] mt-1">{pct}% of target</p>
                      </div>
                    ) : !formatted.hasInlineUnit ? (
                      <p className="text-text-muted text-xs mt-1">{m.unit}</p>
                    ) : null}
                  </Card>
                )
              })}
            </div>
          </section>
        )}

        {/* Weekly Steps Chart */}
        {connected && weekly.length > 0 && (
          <Card>
            <div className="flex items-center gap-2 mb-4">
              <Footprints size={14} className="text-primary" />
              <h2 className="text-text-primary font-semibold text-sm">{t['wearables.weekly_steps']}</h2>
              <span className="text-text-muted text-xs">
                {t['wearables.steps']}
              </span>
            </div>
            <div className="h-48 -ml-2">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={weekly} barCategoryGap="20%">
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                  <XAxis
                    dataKey="day"
                    tick={{ fill: '#94A3B8', fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fill: '#94A3B8', fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                    width={40}
                    tickFormatter={(v: number) => v >= 1000 ? `${(v / 1000).toFixed(0)}k` : String(v)}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1E293B',
                      border: '1px solid rgba(255,255,255,0.1)',
                      borderRadius: '8px',
                      fontSize: '12px',
                    }}
                    labelStyle={{ color: '#CBD5E1' }}
                    itemStyle={{ color: '#60A5FA' }}
                    formatter={(value) => [Number(value).toLocaleString(), t['wearables.steps']]}
                  />
                  <Bar
                    dataKey="steps"
                    fill="#3B82F6"
                    radius={[4, 4, 0, 0]}
                    maxBarSize={40}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        )}

        {/* HealthOS Intelligence */}
        {connected && insight && (
          <Card>
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center shrink-0 mt-0.5">
                <Brain size={16} className="text-primary" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="text-text-primary font-semibold text-sm">{t['wearables.healthos_intelligence']}</h3>
                  <span className="text-[10px] font-medium px-1.5 py-0.5 rounded-full border text-accent bg-accent/10 border-accent/20">
                    AI
                  </span>
                </div>
                <p className="text-text-primary text-sm font-medium mb-2">{insight.title}</p>
                <div className="space-y-2 text-xs">
                  <div className="bg-bg-elevated rounded-lg p-2.5">
                    <p className="text-text-muted uppercase tracking-wide text-[10px] mb-1 font-medium">{t['dashboard.observed_data']}</p>
                    <p className="text-text-secondary">{insight.observed}</p>
                  </div>
                  <div className="bg-accent/5 border border-accent/20 rounded-lg p-2.5">
                    <p className="text-text-muted uppercase tracking-wide text-[10px] mb-1 font-medium">{t['dashboard.suggested_action']}</p>
                    <p className="text-text-secondary">{insight.suggested_action}</p>
                  </div>
                </div>
                <p className="text-text-muted text-xs mt-2 italic">{t['dashboard.ai_disclaimer']}</p>
              </div>
            </div>
          </Card>
        )}

        {/* Data Sources */}
        {connected && device && (
          <Card padding="md">
            <h3 className="text-text-primary font-semibold text-sm mb-3">{t['wearables.data_sources']}</h3>
            <div className="space-y-2">
              <div className="flex items-center justify-between py-2 border-b border-border">
                <div className="flex items-center gap-2">
                  <Watch size={14} className="text-primary" />
                  <span className="text-text-secondary text-xs">{device.device_name}</span>
                </div>
                <span className="text-text-muted text-[10px] font-mono">{device.provider}</span>
              </div>
              <div className="flex items-center justify-between py-2">
                <div className="flex items-center gap-2">
                  <Zap size={14} className="text-accent" />
                  <span className="text-text-secondary text-xs">HealthOS AI Engine</span>
                </div>
                <span className="text-text-muted text-[10px] font-mono">deterministic + mock</span>
              </div>
            </div>
          </Card>
        )}

        {/* Sync History */}
        {connected && syncs.length > 0 && (
          <Card padding="md">
            <div className="flex items-center gap-2 mb-3">
              <Clock size={14} className="text-text-muted" />
              <h3 className="text-text-primary font-semibold text-sm">{t['wearables.sync_history']}</h3>
            </div>
            <div className="space-y-2">
              {syncs.slice(0, 5).map(s => (
                <div key={s.id} className="flex items-center justify-between py-2 border-b border-border last:border-b-0">
                  <div className="flex items-center gap-2">
                    {s.status === 'success' ? (
                      <CheckCircle2 size={14} className="text-accent" />
                    ) : s.status === 'failed' ? (
                      <XCircle size={14} className="text-danger" />
                    ) : (
                      <RefreshCw size={14} className="text-text-muted animate-spin" />
                    )}
                    <div>
                      <p className="text-text-primary text-xs font-medium">
                        {s.status === 'success' ? t['wearables.sync_success'] : s.status === 'failed' ? t['wearables.sync_failed'] : s.status}
                      </p>
                      <p className="text-text-muted text-[10px]">
                        {timeAgo(s.started_at)}
                      </p>
                    </div>
                  </div>
                  <span className="text-text-muted text-[10px]">
                    {t['wearables.records_synced'].replace('{{count}}', String(s.records_synced))}
                  </span>
                </div>
              ))}
            </div>
          </Card>
        )}

      </div>
    </PageWrapper>
  )
}
