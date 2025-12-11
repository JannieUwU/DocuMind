/**
 * Request Cancellation Manager
 *
 * Manages AbortControllers for cancelling pending requests.
 * Prevents response chaos when users switch conversations or navigate quickly.
 *
 * Features:
 * - Per-conversation request tracking
 * - Automatic cleanup of completed requests
 * - Cancel all pending requests
 * - Cancel by conversation ID
 * - Cancel by request type
 */

import { ErrorHandler } from '@/utils/errorHandler'

/**
 * Request types for categorization
 */
export const REQUEST_TYPES = {
  CHAT_MESSAGE: 'chat_message',
  DOCUMENT_UPLOAD: 'document_upload',
  TITLE_GENERATION: 'title_generation',
  FILE_TRANSCRIPTION: 'file_transcription',
  CONVERSATION_LOAD: 'conversation_load'
}

class RequestCancellationManager {
  constructor() {
    /**
     * Map of request identifiers to AbortControllers
     * @type {Map<string, AbortController>}
     */
    this.controllers = new Map()

    /**
     * Map of request identifiers to metadata
     * @type {Map<string, RequestMetadata>}
     */
    this.metadata = new Map()
  }

  /**
   * Create a unique request identifier
   * @param {string} type - Request type
   * @param {string} [conversationId] - Conversation ID
   * @returns {string} Unique identifier
   */
  createRequestId(type, conversationId = null) {
    const id = conversationId
      ? `${type}_${conversationId}`
      : `${type}_${Date.now()}`
    return id
  }

  /**
   * Register a new cancellable request
   * @param {string} type - Request type
   * @param {string} [conversationId] - Conversation ID
   * @returns {{ id: string, controller: AbortController, signal: AbortSignal }}
   */
  register(type, conversationId = null) {
    const requestId = this.createRequestId(type, conversationId)

    // Cancel existing request of the same type for the same conversation
    if (conversationId) {
      this.cancelByConversation(conversationId, type)
    }

    // Create new AbortController
    const controller = new AbortController()

    // Store controller and metadata
    this.controllers.set(requestId, controller)
    this.metadata.set(requestId, {
      type,
      conversationId,
      timestamp: Date.now()
    })

    return {
      id: requestId,
      controller,
      signal: controller.signal
    }
  }

  /**
   * Cancel a specific request
   * @param {string} requestId - Request identifier
   * @param {string} [reason] - Cancellation reason
   * @returns {boolean} True if cancelled
   */
  cancel(requestId, reason = 'Request cancelled') {
    const controller = this.controllers.get(requestId)

    if (controller) {
      try {
        controller.abort(reason)
        this.cleanup(requestId)
        return true
      } catch (error) {
        ErrorHandler.logError(error, 'RequestCancellationManager.cancel')
        return false
      }
    }

    return false
  }

  /**
   * Cancel all requests for a conversation
   * @param {string} conversationId - Conversation ID
   * @param {string} [type] - Optional: only cancel specific type
   * @returns {number} Number of requests cancelled
   */
  cancelByConversation(conversationId, type = null) {
    let cancelledCount = 0

    for (const [requestId, meta] of this.metadata.entries()) {
      if (meta.conversationId === conversationId) {
        // If type specified, only cancel matching type
        if (!type || meta.type === type) {
          if (this.cancel(requestId, `Conversation ${conversationId} changed`)) {
            cancelledCount++
          }
        }
      }
    }

    return cancelledCount
  }

  /**
   * Cancel all requests of a specific type
   * @param {string} type - Request type
   * @returns {number} Number of requests cancelled
   */
  cancelByType(type) {
    let cancelledCount = 0

    for (const [requestId, meta] of this.metadata.entries()) {
      if (meta.type === type) {
        if (this.cancel(requestId, `All ${type} requests cancelled`)) {
          cancelledCount++
        }
      }
    }

    return cancelledCount
  }

  /**
   * Cancel all pending requests
   * @param {string} [reason] - Cancellation reason
   * @returns {number} Number of requests cancelled
   */
  cancelAll(reason = 'All requests cancelled') {
    let cancelledCount = 0

    for (const [requestId] of this.controllers.entries()) {
      if (this.cancel(requestId, reason)) {
        cancelledCount++
      }
    }

    return cancelledCount
  }

  /**
   * Cleanup completed request
   * @param {string} requestId - Request identifier
   */
  cleanup(requestId) {
    this.controllers.delete(requestId)
    this.metadata.delete(requestId)
  }

  /**
   * Check if a request is pending
   * @param {string} requestId - Request identifier
   * @returns {boolean} True if pending
   */
  isPending(requestId) {
    return this.controllers.has(requestId)
  }

  /**
   * Get number of pending requests
   * @returns {number} Pending request count
   */
  getPendingCount() {
    return this.controllers.size
  }

  /**
   * Get pending requests for a conversation
   * @param {string} conversationId - Conversation ID
   * @returns {string[]} Request IDs
   */
  getPendingForConversation(conversationId) {
    const pending = []

    for (const [requestId, meta] of this.metadata.entries()) {
      if (meta.conversationId === conversationId) {
        pending.push(requestId)
      }
    }

    return pending
  }

  /**
   * Get all pending request metadata
   * @returns {Array<{ id: string, type: string, conversationId: string, timestamp: number }>}
   */
  getAllPending() {
    const pending = []

    for (const [requestId, meta] of this.metadata.entries()) {
      pending.push({
        id: requestId,
        ...meta
      })
    }

    return pending
  }

  /**
   * Clear all stored controllers and metadata
   */
  clear() {
    this.controllers.clear()
    this.metadata.clear()
  }

  /**
   * Cleanup old requests (older than specified time)
   * @param {number} maxAge - Maximum age in milliseconds (default: 5 minutes)
   * @returns {number} Number of cleaned up requests
   */
  cleanupOld(maxAge = 5 * 60 * 1000) {
    const now = Date.now()
    let cleanedCount = 0

    for (const [requestId, meta] of this.metadata.entries()) {
      if (now - meta.timestamp > maxAge) {
        this.cancel(requestId, 'Request timeout cleanup')
        cleanedCount++
      }
    }

    return cleanedCount
  }
}

// Export singleton instance
export const requestCancellation = new RequestCancellationManager()

// Export class for testing
export { RequestCancellationManager }

export default requestCancellation
