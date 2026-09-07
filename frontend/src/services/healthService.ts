import api from './api'

export interface HealthStatus {
  ai_provider: string
  ai_model: string | null
}

export async function getHealthStatus(): Promise<HealthStatus> {
  const { data } = await api.get<HealthStatus>('/health')
  return data
}
