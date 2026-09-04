import api from './api'

export interface ProfileData {
  id: string
  user_name: string
  age: number
  sex: string
  height_cm: number
  weight_kg: number
  blood_group: string
  city: string
  language: string
}

export interface ProfileCreateData {
  user_name: string
  age: number
  sex: string
  height_cm: number
  weight_kg: number
  blood_group: string
  city: string
  language: string
}

export async function getProfile(): Promise<ProfileData> {
  const { data } = await api.get<ProfileData>('/profile/me')
  return data
}

export async function createProfile(data: ProfileCreateData): Promise<ProfileData> {
  const { data: profile } = await api.post<ProfileData>('/profile', data)
  return profile
}
