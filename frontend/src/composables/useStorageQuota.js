/**
 * Storage Quota Monitor Composable
 *
 * Monitors localStorage usage and provides warnings.
 */

import { ref, computed, onMounted, onUnmounted } from 'vue'
import chatHistoryManager from '@/services/chatHistoryManager.service'
import { ErrorHandler } from '@/utils/errorHandler'

export function useStorageQuota() {
  const storageInfo = ref({
    used: 0,
    max: 0,
    percentage: 0,
    conversations: 0,
    formattedUsed: '0 Bytes',
    formattedMax: '0 Bytes'
  })

  const isWarningThreshold = computed(() => storageInfo.value.percentage > 60)
  const isDangerThreshold = computed(() => storageInfo.value.percentage > 80)
  const isNearFull = computed(() => storageInfo.value.percentage > 90)

  const statusColor = computed(() => {
    if (isNearFull.value) return 'error'
    if (isDangerThreshold.value) return 'warning'
    if (isWarningThreshold.value) return 'info'
    return 'success'
  })

  const statusMessage = computed(() => {
    if (isNearFull.value) {
      return 'Storage almost full! Cleanup recommended.'
    }
    if (isDangerThreshold.value) {
      return 'Storage usage high. Consider cleaning old conversations.'
    }
    if (isWarningThreshold.value) {
      return 'Storage usage moderate.'
    }
    return 'Storage usage normal.'
  })

  let monitorInterval = null

  /**
   * Update storage information
   */
  function updateStorageInfo() {
    try {
      storageInfo.value = chatHistoryManager.getStorageInfo()
    } catch (error) {
      ErrorHandler.logError(error, 'useStorageQuota.updateStorageInfo')
    }
  }

  /**
   * Perform cleanup
   */
  async function performCleanup() {
    try {
      const success = chatHistoryManager.performCleanup()
      if (success) {
        updateStorageInfo()
        return { success: true, message: 'Cleanup completed successfully' }
      } else {
        return { success: false, message: 'Cleanup failed' }
      }
    } catch (error) {
      ErrorHandler.logError(error, 'useStorageQuota.performCleanup')
      return { success: false, message: 'Cleanup error' }
    }
  }

  /**
   * Clear all history
   */
  async function clearAll() {
    try {
      const success = chatHistoryManager.clear()
      if (success) {
        updateStorageInfo()
        return { success: true, message: 'All history cleared' }
      } else {
        return { success: false, message: 'Clear failed' }
      }
    } catch (error) {
      ErrorHandler.logError(error, 'useStorageQuota.clearAll')
      return { success: false, message: 'Clear error' }
    }
  }

  /**
   * Export history
   */
  function exportHistory() {
    try {
      const jsonString = chatHistoryManager.export()
      const blob = new Blob([jsonString], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `chat-history-${new Date().toISOString().split('T')[0]}.json`
      a.click()
      URL.revokeObjectURL(url)
      return { success: true, message: 'History exported' }
    } catch (error) {
      ErrorHandler.logError(error, 'useStorageQuota.exportHistory')
      return { success: false, message: 'Export failed' }
    }
  }

  /**
   * Import history
   */
  async function importHistory(file) {
    try {
      const text = await file.text()
      const success = chatHistoryManager.import(text)
      if (success) {
        updateStorageInfo()
        return { success: true, message: 'History imported successfully' }
      } else {
        return { success: false, message: 'Import failed - invalid format' }
      }
    } catch (error) {
      ErrorHandler.logError(error, 'useStorageQuota.importHistory')
      return { success: false, message: 'Import error' }
    }
  }

  /**
   * Start monitoring
   */
  function startMonitoring(interval = 30000) {
    updateStorageInfo()
    monitorInterval = setInterval(updateStorageInfo, interval)
  }

  /**
   * Stop monitoring
   */
  function stopMonitoring() {
    if (monitorInterval) {
      clearInterval(monitorInterval)
      monitorInterval = null
    }
  }

  // Auto-start monitoring on mount
  onMounted(() => {
    startMonitoring()
  })

  // Cleanup on unmount
  onUnmounted(() => {
    stopMonitoring()
  })

  return {
    // State
    storageInfo,

    // Computed
    isWarningThreshold,
    isDangerThreshold,
    isNearFull,
    statusColor,
    statusMessage,

    // Methods
    updateStorageInfo,
    performCleanup,
    clearAll,
    exportHistory,
    importHistory,
    startMonitoring,
    stopMonitoring
  }
}
