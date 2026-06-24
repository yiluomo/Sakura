import { apiClient } from './index'
import type { Memory } from '@/types'

export interface MemoryCreateRequest {
  content: string
  category: string
  keywords?: string[]
  importance?: number
}

export interface MemoryUpdateRequest {
  content: string
  category: string
  keywords?: string[]
  importance?: number
}

export interface SystemConfig {
  llm_model: string
  llm_api_key: string
  llm_api_base: string
  
  tts_engine: string
  gpt_weights: string
  sovits_weights: string
  ref_audio_path: string
  prompt_text: string
  prompt_lang: string
  text_lang: string
  speed_factor: number
  
  image_to_text_model: string
  image_to_text_api_key: string
  image_to_text_api_base: string
  
  scene_recognition_model: string
  scene_recognition_api_key: string
  scene_recognition_api_base: string
  
  system_prompt: string
  
  embedding_mode: string
  embedding_api_key: string
  embedding_api_base: string
  embedding_model: string
  embedding_dimension: number
  local_embedding_model: string
  local_embedding_dimension: number
  
  provider_deepseek_key: string
  provider_qwen_key: string
  provider_doubao_key: string
  provider_openai_key: string
  provider_custom_base: string
  provider_custom_key: string
  
  llm_provider: string
  image_to_text_provider: string
  scene_recognition_provider: string
  embedding_provider: string
  
  agent_info?: {
    name: string
    identity: string
    personality: string[]
    hobbies: string[]
    mood: string
    base_prompt: string
    consts: {
      core_contradiction: string
      abilities: string
      forbidden: string
    }
  }
}

export const memoryApi = {
  getMemories: async (): Promise<Memory[]> => {
    const response = await apiClient.get<Memory[]>('/memory')
    return response.data.map((m: any) => ({
      ...m,
      createdAt: m.createdAt ? new Date(m.createdAt) : new Date(),
      updatedAt: m.updatedAt ? new Date(m.updatedAt) : new Date()
    }))
  },

  addMemory: async (data: MemoryCreateRequest): Promise<Memory> => {
    const response = await apiClient.post<Memory>('/memory/create_direct', data)
    return {
      ...response.data,
      createdAt: response.data.createdAt ? new Date(response.data.createdAt) : new Date(),
      updatedAt: response.data.updatedAt ? new Date(response.data.updatedAt) : new Date()
    }
  },

  updateMemory: async (id: string, data: MemoryUpdateRequest): Promise<Memory> => {
    const response = await apiClient.put<Memory>(`/memory/${id}`, data)
    return {
      ...response.data,
      createdAt: response.data.createdAt ? new Date(response.data.createdAt) : new Date(),
      updatedAt: response.data.updatedAt ? new Date(response.data.updatedAt) : new Date()
    }
  },

  deleteMemory: async (id: string): Promise<{ status: string; msg: string }> => {
    const response = await apiClient.delete<{ status: string; msg: string }>(`/memory/${id}`)
    return response.data
  },

  getSystemConfig: async (): Promise<SystemConfig> => {
    const response = await apiClient.get<SystemConfig>('/config')
    return response.data
  },

  updateSystemConfig: async (config: SystemConfig): Promise<{ status: string; msg: string }> => {
    const response = await apiClient.put<{ status: string; msg: string }>('/config', config)
    return response.data
  }
}

