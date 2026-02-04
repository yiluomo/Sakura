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
      id: Date.now().toString(),
      timestamp: new Date(),
    }
    messages.value.push(newMessage)
    return newMessage
  }

  const updateMessage = (id: string, updates: Partial<Message>) => {
    const messageIndex = messages.value.findIndex(msg => msg.id === id)
    if (messageIndex !== -1) {
      messages.value[messageIndex] = { ...messages.value[messageIndex], ...updates }
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
    try {
      error.value = null
      isLoading.value = true

      addMessage({
        role: 'user',
        content,
      })

      const response = await chatApi.sendMessage(content)

      // 始终显示模型回复
      if (response.reply) {
        addMessage({
          role: 'assistant',
          content: response.reply,
        })
      }

      // 返回完整响应（包括可能的记忆信息）
      return response
    } catch (err) {
      error.value = err instanceof Error ? err.message : '发送消息失败'
      const lastMessage = messages.value[messages.value.length - 1]
      if (lastMessage && lastMessage.role === 'user') {
        messages.value.pop()
      }
      throw err
    } finally {
      isLoading.value = false
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
      messages.value = history.map((msg: any, index: number) => ({
        id: Date.now().toString() + index.toString() + Math.random().toString(36).substr(2, 9),
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp ? new Date(msg.timestamp) : new Date(),
      }))
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
        role: 'assistant',
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
  }
})
