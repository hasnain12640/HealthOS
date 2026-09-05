import api from './api'

export type FlowLevel = 'light' | 'moderate' | 'heavy'
export type Severity = 'mild' | 'moderate' | 'severe'
export type SymptomType =
  | 'cramps' | 'headache' | 'bloating' | 'fatigue' | 'mood_changes'
  | 'breast_tenderness' | 'acne' | 'appetite_change' | 'nausea' | 'back_pain' | 'other'
export type CyclePhase = 'menstrual' | 'follicular' | 'ovulatory' | 'luteal'

export interface PeriodDayData {
  date: string
  flow_level: FlowLevel | null
}

export interface CycleData {
  id: string
  start_date: string
  end_date: string | null
  cycle_length: number | null
  period_length: number | null
  notes: string
  created_at: string | null
  period_days: PeriodDayData[]
}

export interface CyclePrediction {
  has_data: boolean
  needs_more_data: boolean
  message: string | null
  current_cycle_day: number | null
  current_phase: CyclePhase | null
  cycle_day_of_phase: number | null
  current_cycle_length: number | null
  average_cycle_length: number | null
  average_period_length: number | null
  cycles_tracked: number
  predicted_period_start: string | null
  predicted_period_end: string | null
  estimated_fertile_start: string | null
  estimated_fertile_end: string | null
  is_on_period_today: boolean
}

export interface CurrentCycleData {
  cycle: CycleData | null
  prediction: CyclePrediction
}

export interface CycleCalendarDay {
  date: string
  in_period: boolean
  is_predicted_period: boolean
  is_fertile_window: boolean
  is_today: boolean
  has_symptom: boolean
  symptom_types: string[]
  flow_level: string | null
}

export interface CycleCalendar {
  month: string
  days: CycleCalendarDay[]
  average_cycle_length: number | null
}

export interface CycleSymptomData {
  id: string
  date: string
  symptom_type: SymptomType
  severity: Severity
  notes: string
  created_at: string | null
}

export async function listCycles(): Promise<CycleData[]> {
  const { data } = await api.get<CycleData[]>('/cycles')
  return data
}

export async function getCurrentCycle(): Promise<CurrentCycleData> {
  const { data } = await api.get<CurrentCycleData>('/cycles/current')
  return data
}

export async function getCyclePrediction(): Promise<CyclePrediction> {
  const { data } = await api.get<CyclePrediction>('/cycles/current/prediction')
  return data
}

export async function getCycleCalendar(year: number, month: number): Promise<CycleCalendar> {
  const { data } = await api.get<CycleCalendar>('/cycles/calendar', {
    params: { year, month },
  })
  return data
}

export async function createCycle(payload: {
  start_date: string
  period_length?: number
  notes?: string
}): Promise<CycleData> {
  const { data } = await api.post<CycleData>('/cycles', payload)
  return data
}

export async function endCycle(cycleId: string, end_date: string): Promise<CycleData> {
  const { data } = await api.post<CycleData>(`/cycles/${cycleId}/end`, { end_date })
  return data
}

export async function listSymptoms(): Promise<CycleSymptomData[]> {
  const { data } = await api.get<CycleSymptomData[]>('/cycle-symptoms')
  return data
}

export async function createSymptom(payload: {
  date: string
  symptom_type: SymptomType
  severity: Severity
  notes?: string
}): Promise<CycleSymptomData> {
  const { data } = await api.post<CycleSymptomData>('/cycle-symptoms', payload)
  return data
}

export async function deleteSymptom(symptomId: string): Promise<{ deleted: boolean; id: string }> {
  const { data } = await api.delete<{ deleted: boolean; id: string }>(`/cycle-symptoms/${symptomId}`)
  return data
}
