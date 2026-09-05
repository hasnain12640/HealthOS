import api from './api'

export interface WearableDevice {
  id: string
  provider: string
  device_name: string
  device_type: string
  status: string
  connected_at: string
  last_synced_at: string | null
}

export interface WearableMetric {
  metric_type: string
  value: number
  unit: string
  source: string
  metadata: { target?: number; sub_text?: string } | null
}

export interface WearableWeeklyDay {
  day: string
  steps: number
}

export interface WearableSyncResult {
  sync_id: string
  status: string
  records_synced: number
  started_at: string
  completed_at: string | null
  error_message: string | null
}

export interface WearableStatusData {
  connected: boolean
  device: {
    connection_id: string
    device_name: string
    device_type: string
    provider: string
    status: string
    last_synced_at: string
    steps: number | null
    resting_heart_rate: number | null
    sleep_hours: number | null
    sleep_score: string | null
    active_calories: number | null
    hydration_liters: number | null
    distance_km: number | null
  } | null
  insight: {
    title: string
    observed: string
    context: string
    suggested_action: string
  } | null
}

export interface WearableSyncHistoryItem {
  id: string
  status: string
  records_synced: number
  started_at: string
  completed_at: string | null
  error_message: string | null
}

export async function listDevices(): Promise<WearableDevice[]> {
  const { data } = await api.get<WearableDevice[]>('/wearables')
  return data
}

export async function getWearableStatus(): Promise<WearableStatusData> {
  const { data } = await api.get<WearableStatusData>('/wearables/status')
  return data
}

export async function demoConnect(): Promise<WearableDevice> {
  const { data } = await api.post<WearableDevice>('/wearables/demo/connect')
  return data
}

export async function syncDevice(connectionId: string): Promise<WearableSyncResult> {
  const { data } = await api.post<WearableSyncResult>(`/wearables/${connectionId}/sync`)
  return data
}

export async function disconnectDevice(connectionId: string): Promise<{ id: string; status: string; device_name: string }> {
  const { data } = await api.post<{ id: string; status: string; device_name: string }>(`/wearables/${connectionId}/disconnect`)
  return data
}

export async function getTodayMetrics(connectionId: string): Promise<WearableMetric[]> {
  const { data } = await api.get<WearableMetric[]>(`/wearables/${connectionId}/metrics/today`)
  return data
}

export async function getWeeklySteps(connectionId: string): Promise<WearableWeeklyDay[]> {
  const { data } = await api.get<WearableWeeklyDay[]>(`/wearables/${connectionId}/metrics/weekly`)
  return data
}

export async function getSyncHistory(connectionId: string): Promise<WearableSyncHistoryItem[]> {
  const { data } = await api.get<WearableSyncHistoryItem[]>(`/wearables/${connectionId}/syncs`)
  return data
}
