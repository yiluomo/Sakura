import { apiClient } from './index'
import type { EmotionState } from '@/types'

export interface ChatRequest {
  user_id?: string
  message: string
}

export interface ChatResponse {
  reply: string | null
  memory_info?: MemoryInfo | null
  audio_url?: string | null      // TTS 生成的音频路径，如 "/audio/xxxx.wav"
  emotion?: EmotionState          // 情绪状态
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

/** GPT-SoVITS 管理接口响应 */
export interface TTSControlResponse {
  status: 'ok' | 'error'
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
   * 导出记忆数据（用于备份或迁移）
   * 返回 JSON 文件的 Blob 对象
   */
  exportMemory: async (userId: string = '依洛沐'): Promise<Blob> => {
    const response = await apiClient.post(`/memory/export`, null, {
      params: { user_id: userId },
      responseType: 'blob'
    })
    return response.data
  },

  /**
   * 导入记忆数据（用于迁移或恢复）
   * @param file 导出的 JSON 文件
   * @param userId 用户 ID
   * @param rebuildVectors 是否重建向量索引
   * @param skipExisting 是否跳过已存在的记录
   */
  importMemory: async (
    file: File,
    userId: string = '依洛沐',
    rebuildVectors: boolean = true,
    skipExisting: boolean = true
  ): Promise<{ status: string; msg: string; imported_count: number; skipped_count: number; vector_count: number }> => {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await apiClient.post(`/memory/import`, formData, {
      params: {
        user_id: userId,
        rebuild_vectors: rebuildVectors,
        skip_existing: skipExisting
      },
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  },

  /**
   * 重建记忆索引
   * 扫描 memory_store/ 目录，将未建立索引的记忆导入数据库
   * @deprecated 已被导出/导入功能替代，保留用于兼容性
   */
  rebuildMemoryIndex: async (): Promise<{ status: string; msg: string; stats: any }> => {
    const response = await apiClient.post<{ status: string; msg: string; stats: any }>('/memory/rebuild')
    return response.data
  },

  /**
   * 查找未建立索引的记忆条目
   * @deprecated 已被导出/导入功能替代，保留用于兼容性
   */
  getUnindexedEntries: async (): Promise<{ status: string; count: number; entries: any[] }> => {
    const response = await apiClient.get<{ status: string; count: number; entries: any[] }>('/memory/unindexed')
    return response.data
  },

  /**
   * 播放音频（传入 audio_url 即可）
   * @param audioUrl  后端返回的 audio_url，如 "/audio/xxxx.wav"
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
    const response = await apiClient.post<{ audio_url: string | null; error?: string }>('/tts', { text })
    const data = response.data as any
    if (data.error) {
      throw new Error(data.error)
    }
    return data.audio_url ?? null
  },

  /**
   * 测试 TTS 服务是否可用
   */
  async testTts(): Promise<{ available: boolean; error?: string }> {
    try {
      const response = await apiClient.post<{ audio_url: string | null; error?: string }>('/tts', { 
        text: '测试' 
      })
      const data = response.data as any
      if (data.error) {
        return { available: false, error: data.error }
      }
      return { available: !!data.audio_url }
    } catch (error: any) {
      return { 
        available: false, 
        error: error.response?.data?.error || error.message || 'TTS 服务不可用' 
      }
    }
  },

  /**
   * 预设参考音频路径（对应 GPT-SoVITS GET /set_refer_audio）
   * 设置成功后，后续 TTS 合成无需重复传 ref_audio_path。
   *
   * @param referAudioPath GPT-SoVITS 服务器端绝对路径（参考音频 3~10 秒）
   */
  async setReferAudio(referAudioPath: string): Promise<TTSControlResponse> {
    const response = await apiClient.post<TTSControlResponse>('/tts/set_refer_audio', {
      refer_audio_path: referAudioPath
    })
    return response.data
  },

  /**
   * 热切换 GPT 模型权重（对应 GPT-SoVITS GET /set_gpt_weights）
   * 无需重启服务，直接切换角色的 GPT 模型（.ckpt 文件）。
   *
   * @param weightsPath .ckpt 文件的绝对或相对路径
   */
  async setGptWeights(weightsPath: string): Promise<TTSControlResponse> {
    const response = await apiClient.post<TTSControlResponse>('/tts/set_gpt_weights', {
      weights_path: weightsPath
    })
    return response.data
  },

  /**
   * 热切换 SoVITS 模型权重（对应 GPT-SoVITS GET /set_sovits_weights）
   * 无需重启服务，直接切换角色的 SoVITS 模型（.pth 文件）。
   *
   * @param weightsPath .pth 文件的绝对或相对路径
   */
  async setSovitsWeights(weightsPath: string): Promise<TTSControlResponse> {
    const response = await apiClient.post<TTSControlResponse>('/tts/set_sovits_weights', {
      weights_path: weightsPath
    })
    return response.data
  }
}
