import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { UIState } from '@/types'

export const useUIStore = defineStore('ui', () => {
  const isDarkMode = ref(false)
  const sidebarCollapsed = ref(false)

  const toggleDarkMode = () => {
    isDarkMode.value = !isDarkMode.value
    localStorage.setItem('darkMode', isDarkMode.value.toString())
  }

  const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  const initializeTheme = () => {
    const savedTheme = localStorage.getItem('darkMode')
    if (savedTheme) {
      isDarkMode.value = savedTheme === 'true'
    } else {
      isDarkMode.value = window.matchMedia('(prefers-color-scheme: dark)').matches
    }
  }

  return {
    isDarkMode,
    sidebarCollapsed,
    toggleDarkMode,
    toggleSidebar,
    initializeTheme,
  }
})
