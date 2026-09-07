import api from './api'

export interface BodyMetrics {
  height_cm: number
  weight_kg: number
  bmi: number
  category: string
  severity: string
}

export interface HydrationAnalysis {
  today_ml: number
  target_ml: number
  percent: number
  status: string
  label: string
  remaining_ml: number
  weekly_avg_ml: number
  logs_today: { id: string; amount_ml: number; source: string }[]
}

export interface NutritionAnalysis {
  total_calories: number
  total_protein_g: number
  total_carbs_g: number
  total_fat_g: number
  meal_count: number
  calorie_target: number
  calorie_percent: number
  protein_target_g: number
  protein_percent: number
  calorie_status: string
  protein_status: string
  meals_today: {
    id: string
    meal_type: string
    food_name: string
    calories: number
    protein_g: number
    carbs_g: number
    fat_g: number
    is_pakistani_food: boolean
  }[]
}

export interface SleepAnalysis {
  avg_hours: number
  status: string
  label: string
  severity: string
  target_hours: number
  deficit_hours: number
  logs: { date: string; hours_slept: number; quality: number }[]
}

export interface ActivityAnalysis {
  sessions: number
  total_minutes: number
  total_steps: number
  weekly_target_min: number
  percent: number
  status: string
  label: string
  recent: { id: string; date: string; activity_type: string; duration_min: number; steps: number; notes: string }[]
}

export interface HealthPriority {
  id: string
  title: string
  observed_data: string
  ai_interpretation: string
  suggested_action: string
  severity: string
  category: string
  source: string
}

export interface AnalysisData {
  profile_id: string
  body_metrics: BodyMetrics
  hydration: HydrationAnalysis
  nutrition: NutritionAnalysis
  sleep: SleepAnalysis
  activity: ActivityAnalysis
  biomarkers: { total: number; abnormal: number; report_id: string | null; report_date: string | null }
  priorities: HealthPriority[]
  priority_count: number
}

export async function getAnalysis(): Promise<AnalysisData> {
  const { data } = await api.get<AnalysisData>('/analysis')
  return data
}
