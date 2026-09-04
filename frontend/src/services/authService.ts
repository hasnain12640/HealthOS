import api from './api'

export interface User {
  id: string
  email: string
  name: string
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterCredentials {
  name: string
  email: string
  password: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export async function login(credentials: LoginCredentials): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>('/auth/login', credentials)
  return data
}

export async function register(credentials: RegisterCredentials): Promise<AuthResponse> {
  const { data } = await api.post<AuthResponse>('/auth/register', credentials)
  return data
}

export async function getMe(): Promise<User> {
  const { data } = await api.get<User>('/auth/me')
  return data
}

export async function logout(): Promise<{ message: string }> {
  const { data } = await api.post<{ message: string }>('/auth/logout')
  return data
}
