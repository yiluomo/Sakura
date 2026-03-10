import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Message, ChatState } from '@/types'
import { chatApi, type MemoryInfo } from '@/api/chat'

export const useChatStore = defineStore('chat', () => {
  const messages = ref<Message[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const chatState = computed<ChatState>(() => ({
    messages: messages.value,
    isLoading: isLoading.value,
    error: error.value,
  }))

  const addMessage = (message: Omit<Message, 'id' | 'timestamp'>) => {
    const newMessage: Message = {
      ...message,
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
    }
    messages.value.push(newMessage)
    return newMessage
  }

  const updateMessage = (id: string, updates: Partial<Message>) => {
    const messageIndex = messages.value.findIndex(msg => msg.id === id)
    if (messageIndex !== -1) {
      console.log('Updating message:', id, 'with:', updates)
      messages.value[messageIndex] = { ...messages.value[messageIndex], ...updates }
    } else {
      console.warn('Message not found for update:', id)
    }
  }

  const deleteMessage = (id: string) => {
    const index = messages.value.findIndex(msg => msg.id === id)
    if (index !== -1) {
      messages.value.splice(index, 1)
    }
  }

  const clearMessages = () => {
    messages.value = []
  }

  const sendMessage = async (content: string) => {
    let assistantMessageId: string | null = null
    
    try {
      error.value = null
      isLoading.value = true

      // 添加用户消息
      const userMessage = addMessage({
        role: 'user',
        content,
      })
      console.log('Added user message:', userMessage.id, userMessage.content)

      const response = await chatApi.sendMessage(content)
      console.log('API response:', response.reply)

      // 如果有回复内容，添加助手消息并开始流式输出
      if (response.reply) {
        // 添加助手消息用于流式输出
        const assistantMessage = addMessage({
          role: 'sakura',
          content: '',
          isStreaming: true,
          audio_url: response.audio_url ?? null,
          emotion: response.emotion, // 设置情绪数据
        })
        assistantMessageId = assistantMessage.id
        console.log('Added assistant message:', assistantMessage.id)

        // 开始流式输出
        await streamText(assistantMessageId, response.reply)
        
        // 流式输出完成后，更新isStreaming状态
        updateMessage(assistantMessageId, {
          isStreaming: false,
        })
      }

      // 返回完整响应（包括可能的记忆信息）
      return response
    } catch (err) {
      error.value = err instanceof Error ? err.message : '发送消息失败'
      
      // 发送失败时移除用户消息
      if (messages.value.length > 0) {
        const lastMessage = messages.value[messages.value.length - 1]
        if (lastMessage && lastMessage.role === 'user') {
          messages.value.pop()
        }
      }
      if (assistantMessageId) {
        deleteMessage(assistantMessageId)
      }
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // 流式文本输出函数
  const streamText = async (messageId: string, text: string) => {
    const chars = text.split('')
    let currentText = ''
    
    for (let i = 0; i < chars.length; i++) {
      currentText += chars[i]
      // 只更新content字段，保持其他属性不变
      updateMessage(messageId, { content: currentText })
      
      // 根据字符类型调整输出速度
      let delay = 30 // 默认延迟
      const char = chars[i]
      
      if (char === '。' || char === '！' || char === '？' || char === '.' || char === '!' || char === '?') {
        delay = 200 // 句号等停顿更长
      } else if (char === '，' || char === '；' || char === '：' || char === ',' || char === ';' || char === ':') {
        delay = 100 // 逗号等中等停顿
      } else if (char === ' ' || char === '\n') {
        delay = 50 // 空格和换行稍微停顿
      } else {
        delay = Math.random() * 20 + 25 // 普通字符随机延迟25-45ms
      }
      
      await new Promise(resolve => setTimeout(resolve, delay))
    }
  }

  const confirmMemory = async (memoryInfo: MemoryInfo, confirmed: boolean) => {
    try {
      error.value = null

      const response = await chatApi.confirmMemory(memoryInfo, confirmed)

      return response
    } catch (err) {
      error.value = err instanceof Error ? err.message : '操作失败'
      throw err
    }
  }

  const retryMessage = async (messageId: string) => {
    const messageIndex = messages.value.findIndex(msg => msg.id === messageId)
    if (messageIndex !== -1) {
      const message = messages.value[messageIndex]
      if (message.role === 'user') {
        messages.value.splice(messageIndex)
        await sendMessage(message.content)
      }
    }
  }

  const fetchHistory = async () => {
    try {
      isLoading.value = true
      const history = await chatApi.getHistory()
      console.log('History data from API:', history) // 调试信息
      
      messages.value = history.map((msg: any, index: number) => {
        console.log(`Message ${index}:`, msg) // 调试每条消息
        
        // 适配后端返回的emotion_type字段，构造完整的emotion对象
        let emotion = null
        if (msg.emotion_type && msg.role === 'sakura') {
          emotion = {
            type: msg.emotion_type,
            mood: 50, // 默认值，因为历史消息中没有存储mood
            energy: 80 // 默认值，因为历史消息中没有存储energy
          }
        }
        
        return {
          id: `${Date.now()}-${index}-${Math.random().toString(36).substr(2, 9)}`,
          role: msg.role,
          content: msg.content,
          timestamp: msg.timestamp ? new Date(msg.timestamp) : new Date(),
          audio_url: msg.audio_url ?? null,
          emotion: emotion, // 使用构造的emotion对象
        }
      })
      
      console.log('Processed messages:', messages.value) // 调试处理后的消息
    } catch (err) {
      error.value = '获取历史记录失败'
    } finally {
      isLoading.value = false
    }
  }

  const saveMemory = async (content: string) => {
    try {
      error.value = null
      isLoading.value = true

      addMessage({
        role: 'user',
        content,
      })

      await chatApi.saveMemory(content)

      addMessage({
        role: 'sakura',
        content: '已将该内容保存至长期记忆。',
      })
    } catch (err) {
      error.value = err instanceof Error ? err.message : '保存记忆失败'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  return {
    messages,
    isLoading,
    error,
    chatState,
    addMessage,
    updateMessage,
    deleteMessage,
    clearMessages,
    sendMessage,
    confirmMemory,
    retryMessage,
    fetchHistory,
    saveMemory,
    streamText, // 导出供测试使用
  }
})
