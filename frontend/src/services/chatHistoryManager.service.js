/**
 * Chat History Manager
 *
 * Manages chat history storage with automatic trimming and cleanup.
 * Prevents localStorage quota exceeded errors.
 *
 * Features:
 * - Automatic conversation limit
 * - Message limit per conversation
 * - Storage quota detection
 * - Automatic cleanup of old data
 * - LRU (Least Recently Used) eviction
 */

import storage from './storage.service'
import { ErrorHandler } from '@/utils/errorHandler'
import { STORAGE_KEYS } from '@/config/constants'

/**
 * @typedef {import('@/types/api.types').ChatConversation} ChatConversation
 * @typedef {import('@/types/api.types').ChatMessage} ChatMessage
 */

/**
 * Storage limits configuration
 */
const STORAGE_LIMITS = {
  MAX_CONVERSATIONS: 50, // Maximum number of conversations to keep
  MAX_MESSAGES_PER_CONVERSATION: 100, // Maximum messages per conversation
  MAX_STORAGE_SIZE: 4 * 1024 * 1024, // 4MB (留出安全边际)
  CLEANUP_THRESHOLD: 0.8, // Cleanup when 80% full
  AUTO_CLEANUP_DAYS: 30 // Auto delete conversations older than 30 days
}

class ChatHistoryManager {
  constructor() {
    this.storageKey = STORAGE_KEYS.CHAT_HISTORY || 'chat-history'
  }

  /**
   * Save chat history with automatic trimming
   * @param {ChatConversation[]} conversations - Conversations to save
   * @returns {boolean} Success status
   */
  save(conversations) {
    try {
      // 1. Clean up old conversations
      let cleaned = this.cleanupOldConversations(conversations)

      // 2. Sort by last activity (most recent first)
      cleaned = this.sortByLastActivity(cleaned)

      // 3. Limit number of conversations
      if (cleaned.length > STORAGE_LIMITS.MAX_CONVERSATIONS) {
        cleaned = cleaned.slice(0, STORAGE_LIMITS.MAX_CONVERSATIONS)
      }

      // 4. Trim messages in each conversation
      cleaned = cleaned.map(conv => this.trimConversation(conv))

      // 5. Check storage size and compress if needed
      const result = this.saveWithSizeCheck(cleaned)

      if (!result.success) {
        // If still too large, perform aggressive cleanup
        cleaned = this.aggressiveCleanup(cleaned)
        return this.saveWithSizeCheck(cleaned).success
      }

      return true
    } catch (error) {
      ErrorHandler.logError(error, 'ChatHistoryManager.save')
      return false
    }
  }

  /**
   * Load chat history
   * @returns {ChatConversation[]} Loaded conversations
   */
  load() {
    try {
      const saved = storage.get(this.storageKey)

      if (!saved || !Array.isArray(saved)) {
        return []
      }

      // Parse dates
      return saved.map(conv => ({
        ...conv,
        created_at: new Date(conv.created_at),
        updated_at: conv.updated_at ? new Date(conv.updated_at) : new Date(conv.created_at),
        messages: conv.messages.map(msg => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        }))
      }))
    } catch (error) {
      ErrorHandler.logError(error, 'ChatHistoryManager.load')
      return []
    }
  }

  /**
   * Add or update a single conversation
   * @param {ChatConversation} conversation - Conversation to save
   */
  saveConversation(conversation) {
    const history = this.load()
    const index = history.findIndex(c => c.id === conversation.id)

    if (index >= 0) {
      history[index] = conversation
    } else {
      history.unshift(conversation) // Add to beginning
    }

    return this.save(history)
  }

  /**
   * Delete a conversation
   * @param {string | number} conversationId - ID of conversation to delete
   */
  deleteConversation(conversationId) {
    const history = this.load()
    const filtered = history.filter(c => c.id !== conversationId)
    return this.save(filtered)
  }

  /**
   * Clean up conversations older than configured days
   * @param {ChatConversation[]} conversations - Conversations to clean
   * @returns {ChatConversation[]} Cleaned conversations
   */
  cleanupOldConversations(conversations) {
    const cutoffDate = new Date()
    cutoffDate.setDate(cutoffDate.getDate() - STORAGE_LIMITS.AUTO_CLEANUP_DAYS)

    return conversations.filter(conv => {
      const lastActivity = new Date(conv.updated_at || conv.created_at)
      return lastActivity > cutoffDate
    })
  }

  /**
   * Sort conversations by last activity
   * @param {ChatConversation[]} conversations - Conversations to sort
   * @returns {ChatConversation[]} Sorted conversations
   */
  sortByLastActivity(conversations) {
    return [...conversations].sort((a, b) => {
      const aTime = new Date(a.updated_at || a.created_at)
      const bTime = new Date(b.updated_at || b.created_at)
      return bTime - aTime // Most recent first
    })
  }

  /**
   * Trim messages in a conversation
   * @param {ChatConversation} conversation - Conversation to trim
   * @returns {ChatConversation} Trimmed conversation
   */
  trimConversation(conversation) {
    if (!conversation.messages || conversation.messages.length <= STORAGE_LIMITS.MAX_MESSAGES_PER_CONVERSATION) {
      return conversation
    }

    // Keep most recent messages
    return {
      ...conversation,
      messages: conversation.messages.slice(-STORAGE_LIMITS.MAX_MESSAGES_PER_CONVERSATION)
    }
  }

  /**
   * Save with size check
   * @param {ChatConversation[]} conversations - Conversations to save
   * @returns {{ success: boolean, size: number }} Result
   */
  saveWithSizeCheck(conversations) {
    const serialized = JSON.stringify(conversations)
    const sizeInBytes = new Blob([serialized]).size

    if (sizeInBytes > STORAGE_LIMITS.MAX_STORAGE_SIZE) {
      return { success: false, size: sizeInBytes }
    }

    const success = storage.set(this.storageKey, conversations)
    return { success, size: sizeInBytes }
  }

  /**
   * Aggressive cleanup when storage is full
   * @param {ChatConversation[]} conversations - Conversations to clean
   * @returns {ChatConversation[]} Aggressively cleaned conversations
   */
  aggressiveCleanup(conversations) {
    // Reduce limits by half
    const reducedConvLimit = Math.floor(STORAGE_LIMITS.MAX_CONVERSATIONS / 2)
    const reducedMsgLimit = Math.floor(STORAGE_LIMITS.MAX_MESSAGES_PER_CONVERSATION / 2)

    return conversations
      .slice(0, reducedConvLimit)
      .map(conv => ({
        ...conv,
        messages: conv.messages.slice(-reducedMsgLimit)
      }))
  }

  /**
   * Get storage usage information
   * @returns {{ used: number, max: number, percentage: number, conversations: number }}
   */
  getStorageInfo() {
    const conversations = this.load()
    const serialized = JSON.stringify(conversations)
    const used = new Blob([serialized]).size
    const max = STORAGE_LIMITS.MAX_STORAGE_SIZE
    const percentage = (used / max) * 100

    return {
      used,
      max,
      percentage: Math.round(percentage * 10) / 10,
      conversations: conversations.length,
      formattedUsed: this.formatBytes(used),
      formattedMax: this.formatBytes(max)
    }
  }

  /**
   * Check if cleanup is needed
   * @returns {boolean} True if cleanup needed
   */
  needsCleanup() {
    const info = this.getStorageInfo()
    return info.percentage > (STORAGE_LIMITS.CLEANUP_THRESHOLD * 100)
  }

  /**
   * Perform manual cleanup
   * @returns {boolean} Success status
   */
  performCleanup() {
    const conversations = this.load()

    // Remove oldest 20% of conversations
    const keepCount = Math.floor(conversations.length * 0.8)
    const cleaned = this.sortByLastActivity(conversations).slice(0, keepCount)

    return this.save(cleaned)
  }

  /**
   * Clear all chat history
   * @returns {boolean} Success status
   */
  clear() {
    try {
      storage.remove(this.storageKey)
      return true
    } catch (error) {
      ErrorHandler.logError(error, 'ChatHistoryManager.clear')
      return false
    }
  }

  /**
   * Export chat history as JSON
   * @returns {string} JSON string
   */
  export() {
    const conversations = this.load()
    return JSON.stringify(conversations, null, 2)
  }

  /**
   * Import chat history from JSON
   * @param {string} jsonString - JSON string to import
   * @returns {boolean} Success status
   */
  import(jsonString) {
    try {
      const conversations = JSON.parse(jsonString)

      if (!Array.isArray(conversations)) {
        throw new Error('Invalid format: expected array of conversations')
      }

      return this.save(conversations)
    } catch (error) {
      ErrorHandler.logError(error, 'ChatHistoryManager.import')
      return false
    }
  }

  /**
   * Format bytes to human-readable string
   * @param {number} bytes - Bytes to format
   * @returns {string} Formatted string
   */
  formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes'

    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  /**
   * Get storage limits configuration
   * @returns {typeof STORAGE_LIMITS} Configuration
   */
  getLimits() {
    return { ...STORAGE_LIMITS }
  }

  /**
   * Update storage limits (for testing or customization)
   * @param {Partial<typeof STORAGE_LIMITS>} limits - New limits
   */
  updateLimits(limits) {
    Object.assign(STORAGE_LIMITS, limits)
  }
}

// Export singleton instance
export const chatHistoryManager = new ChatHistoryManager()

// Export class for testing
export { ChatHistoryManager, STORAGE_LIMITS }

export default chatHistoryManager
