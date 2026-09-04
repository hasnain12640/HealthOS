import api from './api'

export interface DashboardData {
  profile: {
    id: string
    user_name: string
    age: number
    sex: string
    city: string
    language: string
    bmi: number
    bmi_category: string
  }
  lab_summary: {
    report_id: string | null
    lab_name: string | null
    report_date: string | null
    total_biomarkers: number
    abnormal_count: number
    biomarkers: Array<{
      id: string
      name: string
      value: number
      unit: string
      reference_low: number | null
      reference_high: number | null
      status: 'normal' | 'low' | 'high' | 'critical'
      category: string
    }>
  }
  hydration: {
    today_ml: number
    target_ml: number
    percent: number
    logs: Array<{ id: string; amount_ml: number; source: string; date: string }>
  }
  nutrition: {
    total_calories: number
    total_protein_g: number
    total_carbs_g: number
    total_fat_g: number
    meal_count: number
    meals: Array<{
      id: string
      meal_type: string
      food_name: string
      calories: number
      protein_g: number
      is_pakistani_food: boolean
    }>
  }
  sleep: {
    avg_hours: number
    target_hours: number
    logs: Array<{ date: string; hours_slept: number; quality: number }>
  }
  activity: {
    recent: Array<{
      id: string
      date: string
      activity_type: string
      duration_min: number
      steps: number
    }>
  }
  priorities: Array<{
    id: string
    title: string
    observed_data: string
    ai_interpretation: string
    suggested_action: string
    severity: 'low' | 'medium' | 'high'
    category: string
  }>
  timeline: Array<{
    id: string
    date: string
    event_type: string
    title: string
    description: string
    is_ai_generated: boolean
  }>
  ai_insight: {
    text: string
    generated_by: string
    date: string
  }
}

export async function getDashboard(): Promise<DashboardData> {
  const res = await api.get<DashboardData>('/dashboard')
  return res.data
}
