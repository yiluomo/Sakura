export interface EmotionState {
  type: 'calm' | 'happy' | 'melancholy' | 'nostalgic' | 'guarded'
  mood: number
  energy: number
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  error?: string
  audio_url?: string | null   // TTS 生成的音频路径
  emotion?: EmotionState      // 情绪状态（仅 assistant 消息有）
}

export interface ChatState {
  messages: Message[]
  isLoading: boolean
  error: string | null
}

export interface UIState {
  isDarkMode: boolean
  sidebarCollapsed: boolean
}
