/**
 * Global Error Handler Plugin
 *
 * Catches unhandled errors and promise rejections globally.
 */

import { ErrorHandler } from '@/utils/errorHandler'

/**
 * Install global error handlers
 * @param {import('vue').App} app - Vue app instance
 */
export function setupErrorHandlers(app) {
  // Vue error handler
  app.config.errorHandler = (err, instance, info) => {
    ErrorHandler.logError(err, `Vue Error [${info}]`)

    // Show error to user in development
    if (import.meta.env.DEV) {
      console.error('Vue Error:', err)
      console.error('Component:', instance)
      console.error('Info:', info)
    }
  }

  // Vue warning handler (dev only)
  if (import.meta.env.DEV) {
    app.config.warnHandler = (msg, instance, trace) => {
      console.warn('Vue Warning:', msg)
      console.warn('Trace:', trace)
    }
  }

  // Global unhandled error
  window.addEventListener('error', (event) => {
    ErrorHandler.logError(event.error, 'Unhandled Error')

    // Prevent default browser error handling
    event.preventDefault()
  })

  // Global unhandled promise rejection
  window.addEventListener('unhandledrejection', (event) => {
    ErrorHandler.logError(event.reason, 'Unhandled Promise Rejection')

    // Prevent default browser handling
    event.preventDefault()
  })
}

/**
 * Create error boundary composable
 * Use in components to handle errors gracefully
 */
export function useErrorBoundary() {
  const { ref } = require('vue')

  const error = ref(null)
  const isError = ref(false)

  /**
   * Execute function with error handling
   * @template T
   * @param {() => Promise<T>} fn - Async function to execute
   * @returns {Promise<T | null>}
   */
  const execute = async (fn) => {
    try {
      error.value = null
      isError.value = false
      return await fn()
    } catch (err) {
      const appError = ErrorHandler.handleApiError(err)
      error.value = ErrorHandler.getUserMessage(appError)
      isError.value = true
      ErrorHandler.logError(appError, 'ErrorBoundary')
      return null
    }
  }

  /**
   * Clear error state
   */
  const clearError = () => {
    error.value = null
    isError.value = false
  }

  return {
    error,
    isError,
    execute,
    clearError
  }
}

export default {
  setupErrorHandlers,
  useErrorBoundary
}
