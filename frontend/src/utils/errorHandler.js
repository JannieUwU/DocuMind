/**
 * Error Handling Utilities
 *
 * Provides consistent error handling across the application.
 * @typedef {import('@/types/api.types').ErrorResponse} ErrorResponse
 */

import { HTTP_STATUS, ERROR_MESSAGES } from '@/config/constants'

/**
 * Application Error Class
 * Custom error class with additional context
 */
export class AppError extends Error {
  /**
   * @param {string} message - Error message
   * @param {string} code - Error code
   * @param {number} [statusCode] - HTTP status code
   * @param {any} [details] - Additional error details
   */
  constructor(message, code, statusCode, details) {
    super(message)
    this.name = 'AppError'
    this.code = code
    this.statusCode = statusCode
    this.details = details
    this.timestamp = new Date().toISOString()

    // Maintains proper stack trace for where error was thrown (V8 only)
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, AppError)
    }
  }

  /**
   * Convert to JSON representation
   * @returns {ErrorResponse}
   */
  toJSON() {
    return {
      success: false,
      error: this.message,
      code: this.code,
      statusCode: this.statusCode,
      detail: this.details,
    }
  }

  /**
   * Get user-friendly message
   * @returns {string}
   */
  getUserMessage() {
    return this.message || ERROR_MESSAGES.UNKNOWN_ERROR
  }
}

/**
 * Specific error types
 */
export class AuthenticationError extends AppError {
  constructor(message = ERROR_MESSAGES.INVALID_CREDENTIALS) {
    super(message, 'AUTH_ERROR', HTTP_STATUS.UNAUTHORIZED)
  }
}

export class ValidationError extends AppError {
  /**
   * @param {string} message
   * @param {Record<string, string>} [fieldErrors]
   */
  constructor(message, fieldErrors) {
    super(message, 'VALIDATION_ERROR', HTTP_STATUS.BAD_REQUEST, fieldErrors)
  }
}

export class NetworkError extends AppError {
  constructor(message = ERROR_MESSAGES.NETWORK_ERROR) {
    super(message, 'NETWORK_ERROR')
  }
}

export class TimeoutError extends AppError {
  constructor(message = ERROR_MESSAGES.TIMEOUT) {
    super(message, 'TIMEOUT')
  }
}

export class ServerError extends AppError {
  constructor(message = ERROR_MESSAGES.SERVER_ERROR) {
    super(message, 'SERVER_ERROR', HTTP_STATUS.INTERNAL_SERVER_ERROR)
  }
}

export class NotFoundError extends AppError {
  constructor(message = 'Resource not found') {
    super(message, 'NOT_FOUND', HTTP_STATUS.NOT_FOUND)
  }
}

export class RateLimitError extends AppError {
  constructor(message = '请求过于频繁，请稍后再试') {
    super(message, 'RATE_LIMIT', 429)
  }
}

/**
 * Error Handler Class
 * Centralized error handling logic
 */
export class ErrorHandler {
  /**
   * Handle API errors from axios
   * @param {any} error - Axios error object
   * @returns {AppError}
   */
  static handleApiError(error) {
    // Network error (no response)
    if (!error.response) {
      if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
        return new TimeoutError()
      }
      return new NetworkError()
    }

    const { status, data } = error.response

    // Handle different status codes
    switch (status) {
      case HTTP_STATUS.UNAUTHORIZED:
        return new AuthenticationError(
          data?.detail || data?.message || ERROR_MESSAGES.SESSION_EXPIRED
        )

      case HTTP_STATUS.FORBIDDEN:
        return new AppError(
          data?.detail || '没有权限执行此Actions',
          'FORBIDDEN',
          HTTP_STATUS.FORBIDDEN
        )

      case HTTP_STATUS.NOT_FOUND:
        return new NotFoundError(data?.detail || '请求的资源不存在')

      case HTTP_STATUS.BAD_REQUEST:
        return new ValidationError(
          data?.detail || data?.message || '请求参数Error',
          data?.errors
        )

      case HTTP_STATUS.CONFLICT:
        return new AppError(
          data?.detail || '资源冲突',
          'CONFLICT',
          HTTP_STATUS.CONFLICT
        )

      case 429:
        return new RateLimitError(data?.detail)

      case HTTP_STATUS.INTERNAL_SERVER_ERROR:
      case HTTP_STATUS.SERVICE_UNAVAILABLE:
        return new ServerError(data?.detail || data?.message)

      default:
        return new AppError(
          data?.detail || data?.message || ERROR_MESSAGES.UNKNOWN_ERROR,
          'API_ERROR',
          status,
          data
        )
    }
  }

  /**
   * Handle validation errors
   * @param {Record<string, string>} errors - Field-level errors
   * @returns {ValidationError}
   */
  static handleValidationError(errors) {
    const messages = Object.values(errors).join(', ')
    return new ValidationError(messages, errors)
  }

  /**
   * Log error to console (can be extended to send to logging service)
   * @param {Error} error
   * @param {string} [context] - Context where error occurred
   */
  static logError(error, context) {
    const timestamp = new Date().toISOString()

    if (error instanceof AppError) {
      console.error(`[${timestamp}] [${context || 'App'}] AppError:`, {
        message: error.message,
        code: error.code,
        statusCode: error.statusCode,
        details: error.details,
        stack: error.stack
      })
    } else {
      console.error(`[${timestamp}] [${context || 'App'}] Error:`, {
        message: error.message,
        stack: error.stack
      })
    }

    // In production, send to error tracking service
    // e.g., Sentry, LogRocket, etc.
    if (import.meta.env.PROD) {
      // Example: Sentry.captureException(error)
    }
  }

  /**
   * Get user-friendly error message
   * @param {Error | AppError} error
   * @returns {string}
   */
  static getUserMessage(error) {
    if (error instanceof AppError) {
      return error.getUserMessage()
    }

    // Generic error message for unknown errors
    return ERROR_MESSAGES.UNKNOWN_ERROR
  }

  /**
   * Check if error is retryable
   * @param {Error | AppError} error
   * @returns {boolean}
   */
  static isRetryable(error) {
    if (!(error instanceof AppError)) {
      return false
    }

    // Network errors and timeouts are retryable
    const retryableCodes = ['NETWORK_ERROR', 'TIMEOUT', 'SERVER_ERROR']
    return retryableCodes.includes(error.code)
  }

  /**
   * Check if error requires authentication
   * @param {Error | AppError} error
   * @returns {boolean}
   */
  static requiresAuth(error) {
    return error instanceof AuthenticationError ||
           (error instanceof AppError && error.statusCode === HTTP_STATUS.UNAUTHORIZED)
  }
}

/**
 * Utility function to safely execute async operations with error handling
 * @template T
 * @param {() => Promise<T>} operation - Async operation to execute
 * @param {string} [context] - Context for logging
 * @returns {Promise<{data: T | null, error: AppError | null}>}
 */
export async function safeAsync(operation, context) {
  try {
    const data = await operation()
    return { data, error: null }
  } catch (err) {
    const error = ErrorHandler.handleApiError(err)
    ErrorHandler.logError(error, context)
    return { data: null, error }
  }
}

/**
 * Retry utility with exponential backoff
 * @template T
 * @param {() => Promise<T>} operation - Operation to retry
 * @param {Object} options - Retry options
 * @param {number} [options.maxRetries=3] - Maximum retry attempts
 * @param {number} [options.initialDelay=1000] - Initial delay in ms
 * @param {number} [options.maxDelay=10000] - Maximum delay in ms
 * @param {(error: Error) => boolean} [options.shouldRetry] - Custom retry logic
 * @returns {Promise<T>}
 */
export async function retryWithBackoff(operation, options = {}) {
  const {
    maxRetries = 3,
    initialDelay = 1000,
    maxDelay = 10000,
    shouldRetry = ErrorHandler.isRetryable
  } = options

  let lastError

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await operation()
    } catch (error) {
      lastError = ErrorHandler.handleApiError(error)

      // Don't retry if not retryable or last attempt
      if (!shouldRetry(lastError) || attempt === maxRetries) {
        throw lastError
      }

      // Calculate delay with exponential backoff
      const delay = Math.min(initialDelay * Math.pow(2, attempt), maxDelay)

      console.warn(`Retry attempt ${attempt + 1}/${maxRetries} after ${delay}ms`)

      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, delay))
    }
  }

  throw lastError
}

/**
 * Create error from response
 * @param {any} response - API response
 * @returns {AppError | null}
 */
export function createErrorFromResponse(response) {
  if (!response || response.success) {
    return null
  }

  return new AppError(
    response.error || response.message || ERROR_MESSAGES.UNKNOWN_ERROR,
    response.code || 'API_ERROR',
    response.statusCode,
    response.detail
  )
}

// Export all error classes
export default {
  AppError,
  AuthenticationError,
  ValidationError,
  NetworkError,
  TimeoutError,
  ServerError,
  NotFoundError,
  RateLimitError,
  ErrorHandler,
  safeAsync,
  retryWithBackoff,
  createErrorFromResponse,
}
