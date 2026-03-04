import { apiClient } from './index'

export interface ChatRequest {
  user_id?: string
  message: string
}

export interface ChatResponse {
  reply: string | null
  memory_info?: MemoryInfo | null
  audio_url?: string | null      // TTS 生成的音频路径，如 "/audio/xxxx.mp3"
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
  },

  archiveMemory: async (userId: string = '依洛沐'): Promise<{ status: string; msg: string; archived_count: number }> => {
    const response = await apiClient.post(`/memory/archive`, null, {
      params: { user_id: userId }
    })
    return response.data as { status: string; msg: string; archived_count: number }
  },

  /**
   * 播放音频（传入 audio_url 即可）
   * @param audioUrl  后端返回的 audio_url，如 "/audio/xxxx.mp3"
   */
  playAudio(audioUrl: string | null | undefined): HTMLAudioElement | null {
    if (!audioUrl) return null
    const audio = new Audio(`http://localhost:8000${audioUrl}`)
    audio.play().catch(e => console.warn('[TTS] 播放失败:', e))
    return audio
  },

  /**
   * 按需生成 TTS 音频（无缓存时调用后端接口，有缓存直接命中）
   * @param text 要合成的文本
   */
  async generateTts(text: string): Promise<string | null> {
    const response = await apiClient.post<{ audio_url: string | null }>('/tts', { text })
    return (response.data as any).audio_url ?? null
  }
}
