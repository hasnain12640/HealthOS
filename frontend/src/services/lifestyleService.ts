import api from './api'

export interface HydrationLogInput {
  date: string
  amount_ml: number
  source?: string
}

export interface HydrationLogResponse {
  id: string
  profile_id: string
  date: string
  amount_ml: number
  source: string
}

export interface NutritionLogInput {
  date: string
  meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack' | 'meal' | 'other'
  food_name: string
  quantity_g: number
  calories: number
  protein_g: number
  carbs_g: number
  fat_g: number
  is_pakistani_food: boolean
}

export interface NutritionLogResponse extends NutritionLogInput {
  id: string
  profile_id: string
}

export interface SleepLogInput {
  date: string
  hours_slept: number
  quality: number
}

export interface SleepLogResponse extends SleepLogInput {
  id: string
  profile_id: string
}

export interface ActivityLogInput {
  date: string
  activity_type: string
  duration_min: number
  steps: number
  notes: string
}

export interface ActivityLogResponse extends ActivityLogInput {
  id: string
  profile_id: string
}

export async function logHydration(input: HydrationLogInput): Promise<HydrationLogResponse> {
  const { data } = await api.post<HydrationLogResponse>('/lifestyle/hydration', {
    ...input,
    source: input.source ?? 'water',
  })
  return data
}

export async function logNutrition(input: NutritionLogInput): Promise<NutritionLogResponse> {
  const { data } = await api.post<NutritionLogResponse>('/lifestyle/nutrition', input)
  return data
}

export async function logSleep(input: SleepLogInput): Promise<SleepLogResponse> {
  const { data } = await api.post<SleepLogResponse>('/lifestyle/sleep', input)
  return data
}

export async function logActivity(input: ActivityLogInput): Promise<ActivityLogResponse> {
  const { data } = await api.post<ActivityLogResponse>('/lifestyle/activity', input)
  return data
}
