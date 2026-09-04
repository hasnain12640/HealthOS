import api from './api'
import type { DayPlan } from '../types'

export interface GeneratedPlan {
  plan: {
    summary: string
    days: DayPlan[]
  }
  provider: string
  generated_at: string
}

export interface InsightData {
  text: string
  provider: string
  date: string
}

export async function generatePlan(): Promise<GeneratedPlan> {
  const { data } = await api.post<GeneratedPlan>('/plan', {}, { timeout: 60000 })
  return data
}

export async function getInsight(): Promise<InsightData> {
  const { data } = await api.post<InsightData>('/insights', {}, { timeout: 60000 })
  return data
}
