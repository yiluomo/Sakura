import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { UIState } from '@/types'
import type { ErrorInfo } from '@/utils/errorHandler'

export const useUIStore = defineStore('ui', () => {
  const isDarkMode = ref(false)
  const sidebarCollapsed = ref(false)
  // TTS 自动播放开关（默认关闭，持久化到 localStorage）
  const ttsAutoPlay = ref(
    localStorage.getItem('ttsAutoPlay') === 'true'
  )
  
  // 错误提示状态
  const errorToast = ref<ErrorInfo & { visible: boolean }>({
    visible: false,
    title: '',
    message: '',
    type: 'error'
  })

  const toggleDarkMode = () => {
    isDarkMode.value = !isDarkMode.value
    localStorage.setItem('darkMode', isDarkMode.value.toString())
  }

  const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  const toggleTtsAutoPlay = () => {
    ttsAutoPlay.value = !ttsAutoPlay.value
    localStorage.setItem('ttsAutoPlay', ttsAutoPlay.value.toString())
  }

  const initializeTheme = () => {
    const savedTheme = localStorage.getItem('darkMode')
    if (savedTheme) {
      isDarkMode.value = savedTheme === 'true'
    } else {
      isDarkMode.value = window.matchMedia('(prefers-color-scheme: dark)').matches
    }
  }

  const showError = (error: ErrorInfo) => {
    errorToast.value = {
      ...error,
      visible: true
    }
  }

  const hideError = () => {
    errorToast.value.visible = false
  }

  return {
    isDarkMode,
    sidebarCollapsed,
    ttsAutoPlay,
    errorToast,
    toggleDarkMode,
    toggleSidebar,
    toggleTtsAutoPlay,
    initializeTheme,
    showError,
    hideError,
  }
})
