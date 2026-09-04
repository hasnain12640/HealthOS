import api from './api'

export interface ChatHistoryItem {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatResponse {
  reply: string
  provider: string
}

export async function sendChatMessage(
  message: string,
  history: ChatHistoryItem[]
): Promise<ChatResponse> {
  const { data } = await api.post<ChatResponse>(
    '/chat',
    { message, history },
    { timeout: 60000 }
  )
  return data
}
