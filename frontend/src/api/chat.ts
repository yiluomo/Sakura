import { apiClient } from './index'

export interface ChatRequest {
  user_id?: string
  message: string
}

export interface ChatResponse {
  reply: string | null
  memory_info?: MemoryInfo | null
}

export interface MemoryInfo {
  action: 'create' | 'update'
  memory_type: string
  key: string
  value?: string
  old_value?: string
  new_value?: string
  importance: number
}

export interface MemoryConfirmRequest {
  user_id?: string
  memory_info: MemoryInfo
  confirmed: boolean
}

export interface MemoryConfirmResponse {
  status: string
  reply?: string
  msg: string
}

export const chatApi = {
  sendMessage: async (message: string, userId: string = '依洛沐'): Promise<ChatResponse> => {
    const response = await apiClient.post<ChatResponse>('/chat', {
      user_id: userId,
      message: message
    })
    return response.data
  },

  getHistory: async (userId: string = '依洛沐'): Promise<any[]> => {
    const response = await apiClient.get<any[]>('/history', {
      params: { user_id: userId }
    })
    return response.data
  },

  saveMemory: async (content: string, userId: string = '依洛沐'): Promise<any> => {
    const response = await apiClient.post('/memory', {
      user_id: userId,
      content: content
    })
    return response.data
  },

  confirmMemory: async (memoryInfo: MemoryInfo, confirmed: boolean, userId: string = '依洛沐'): Promise<MemoryConfirmResponse> => {
    const response = await apiClient.post<MemoryConfirmResponse>('/memory/confirm', {
      user_id: userId,
      memory_info: memoryInfo,
      confirmed: confirmed
    })
    return response.data
  }
}
