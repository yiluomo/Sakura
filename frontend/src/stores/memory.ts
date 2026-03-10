import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Memory } from '@/types'

export const useMemoryStore = defineStore('memory', () => {
  const memories = ref<Memory[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const addMemory = async (memoryData: Omit<Memory, 'id' | 'createdAt' | 'updatedAt'>) => {
    try {
      isLoading.value = true
      error.value = null
      
      const newMemory: Memory = {
        ...memoryData,
        id: Date.now().toString(),
        createdAt: new Date(),
        updatedAt: new Date(),
      }
      
      memories.value.push(newMemory)
    } catch (err) {
      error.value = err instanceof Error ? err.message : '添加记忆失败'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const updateMemory = async (id: string, updates: Omit<Memory, 'id' | 'createdAt' | 'updatedAt'>) => {
    try {
      isLoading.value = true
      error.value = null
      
      const index = memories.value.findIndex(m => m.id === id)
      if (index !== -1) {
        memories.value[index] = {
          ...memories.value[index],
          ...updates,
          updatedAt: new Date(),
        }
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '更新记忆失败'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const deleteMemory = async (id: string) => {
    try {
      isLoading.value = true
      error.value = null
      
      const index = memories.value.findIndex(m => m.id === id)
      if (index !== -1) {
        memories.value.splice(index, 1)
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '删除记忆失败'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const loadMemories = async () => {
    try {
      isLoading.value = true
      error.value = null
      
      // 这里应该调用API加载记忆数据
      // 暂时使用空数组
      memories.value = []
    } catch (err) {
      error.value = err instanceof Error ? err.message : '加载记忆失败'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  return {
    memories,
    isLoading,
    error,
    addMemory,
    updateMemory,
    deleteMemory,
    loadMemories,
  }
})