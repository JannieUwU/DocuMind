/**
 * Theme Management Composable
 *
 * Manages dark/light theme state and persistence.
 */

import { ref, watch, onMounted } from 'vue'
import storage from '@/services/storage.service'
import { STORAGE_KEYS } from '@/config/constants'

export function useTheme() {
  const isDark = ref(false)

  /**
   * Initialize theme from storage or system preference
   */
  function initTheme() {
    const storedTheme = storage.get(STORAGE_KEYS.THEME)

    if (storedTheme !== null) {
      isDark.value = storedTheme === 'dark'
    } else {
      // Check system preference
      isDark.value = window.matchMedia('(prefers-color-scheme: dark)').matches
    }

    applyTheme()
  }

  /**
   * Apply theme to document
   */
  function applyTheme() {
    if (isDark.value) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  /**
   * Toggle theme
   */
  function toggleTheme() {
    isDark.value = !isDark.value
  }

  /**
   * Set theme explicitly
   * @param {boolean} dark - Whether to use dark theme
   */
  function setTheme(dark) {
    isDark.value = dark
  }

  // Watch theme changes and persist
  watch(isDark, (newValue) => {
    applyTheme()
    storage.set(STORAGE_KEYS.THEME, newValue ? 'dark' : 'light')
  })

  // Initialize on mount
  onMounted(() => {
    initTheme()

    // Listen for system theme changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    mediaQuery.addEventListener('change', (e) => {
      // Only apply system preference if no stored preference
      if (storage.get(STORAGE_KEYS.THEME) === null) {
        isDark.value = e.matches
      }
    })
  })

  return {
    isDark,
    toggleTheme,
    setTheme,
    initTheme
  }
}
