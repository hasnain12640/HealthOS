import api from './api'

interface HydrationLogResponse {
  id: string
  profile_id: string
  date: string
  amount_ml: number
  source: string
}

export async function logHydration(amountMl: number): Promise<HydrationLogResponse> {
  const { data } = await api.post<HydrationLogResponse>('/lifestyle/hydration', {
    date: new Date().toISOString().slice(0, 10),
    amount_ml: amountMl,
    source: 'water',
  })
  return data
}
