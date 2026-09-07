import api from './api'

export interface HistoryProfile {
  id: string
  user_name: string
  age: number
  sex: string
  weight_kg: number
  height_cm: number
  bmi: number
  bmi_category: string
}

export interface HistoryWearableDay {
  steps: number | null
  active_calories: number | null
  resting_heart_rate: number | null
  avg_heart_rate: number | null
  sleep_hours: number | null
  distance_km: number | null
  water_ml: number | null
  weight_kg: number | null
}

export interface HistoryHydration {
  amount_ml: number
  target_ml: number
  percent: number
  status: string
  label: string
}

export interface HistorySleep {
  hours_slept: number
  quality: number
  status: string
  label: string
}

export interface HistoryActivity {
  steps: number
  duration_min: number
  sessions: number
}

export interface HistoryNutrition {
  total_calories: number
  total_protein_g: number
  total_carbs_g: number
  total_fat_g: number
  meal_count: number
}

export interface HistoryBiomarker {
  id: string
  name: string
  value: number
  unit: string
  reference_low: number | null
  reference_high: number | null
  status: 'normal' | 'low' | 'high' | 'critical'
  category: string
}

export interface HistoryLabReport {
  id: string
  lab_name: string
  report_date: string
  upload_date: string
  biomarkers: HistoryBiomarker[]
}

export interface HistoryEvent {
  id: string
  event_type: string
  title: string
  description: string
  is_ai_generated: boolean
}

export interface HistoryCycle {
  phase: string
  phase_day: number
  cycle_day: number
  is_period: boolean
  flow_level: string | null
  is_fertile_window: boolean
  symptoms: string[]
}

export interface HistoryDay {
  date: string
  is_today: boolean
  wearable: HistoryWearableDay
  hydration: HistoryHydration
  sleep: HistorySleep | null
  activity: HistoryActivity
  nutrition: HistoryNutrition
  labs: HistoryLabReport[]
  events: HistoryEvent[]
  cycle?: HistoryCycle | null
}

export interface HistoryPriority {
  id: string
  title: string
  observed_data: string
  ai_interpretation: string
  suggested_action: string
  severity: 'low' | 'medium' | 'high'
  category: string
}

export interface HistoryAIInsight {
  text: string | null
  generated_by: string
  date: string
}

export interface HistorySummary {
  days_count: number
  avg_steps: number
  avg_sleep_hours: number
  avg_hydration_percent: number
  avg_hydration_ml: number
  total_activity_minutes: number
  total_reports: number
  total_biomarkers: number
  abnormal_biomarker_count: number
  period_days: number
  fertile_window_days: number
  priorities: HistoryPriority[]
  ai_insight: HistoryAIInsight | null
}

export interface HistoryWearableSummary {
  connection_id: string
  device_name: string
  device_type: string
  provider: string
  last_synced_at: string
}

export interface HistoryData {
  profile: HistoryProfile
  days: number
  date_range: { start: string; end: string }
  summary: HistorySummary
  wearable: HistoryWearableSummary | null
  daily: HistoryDay[]
}

export async function getHistory(days = 30): Promise<HistoryData> {
  const res = await api.get<HistoryData>('/history', { params: { days } })
  return res.data
}
