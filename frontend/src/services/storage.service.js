/**
 * Storage Service - Unified abstraction layer for browser storage
 *
 * Features:
 * - Consistent error handling
 * - Type-safe get/set operations
 * - Easy to swap implementations (localStorage, sessionStorage, IndexedDB)
 * - Automatic JSON serialization/deserialization
 */

class StorageService {
  constructor(storage = localStorage) {
    this.storage = storage
  }

  /**
   * Get item from storage
   * @template T
   * @param {string} key - Storage key
   * @param {T} [defaultValue=null] - Default value if key doesn't exist
   * @returns {T|null} Parsed value or default
   */
  get(key, defaultValue = null) {
    try {
      const item = this.storage.getItem(key)
      if (item === null) {
        return defaultValue
      }

      // Try to parse as JSON, fall back to raw string
      try {
        return JSON.parse(item)
      } catch {
        return item
      }
    } catch (error) {
      console.error(`[Storage] Error reading key "${key}":`, error)
      return defaultValue
    }
  }

  /**
   * Set item in storage
   * @template T
   * @param {string} key - Storage key
   * @param {T} value - Value to store
   * @returns {boolean} Success status
   */
  set(key, value) {
    try {
      const serialized = typeof value === 'string'
        ? value
        : JSON.stringify(value)

      this.storage.setItem(key, serialized)
      return true
    } catch (error) {
      console.error(`[Storage] Error writing key "${key}":`, error)

      // Handle quota exceeded error
      if (error.name === 'QuotaExceededError') {
        console.warn('[Storage] Storage quota exceeded')
      }

      return false
    }
  }

  /**
   * Remove item from storage
   * @param {string} key - Storage key
   * @returns {boolean} Success status
   */
  remove(key) {
    try {
      this.storage.removeItem(key)
      return true
    } catch (error) {
      console.error(`[Storage] Error removing key "${key}":`, error)
      return false
    }
  }

  /**
   * Check if key exists in storage
   * @param {string} key - Storage key
   * @returns {boolean}
   */
  has(key) {
    try {
      return this.storage.getItem(key) !== null
    } catch (error) {
      console.error(`[Storage] Error checking key "${key}":`, error)
      return false
    }
  }

  /**
   * Clear all items from storage
   * @returns {boolean} Success status
   */
  clear() {
    try {
      this.storage.clear()
      return true
    } catch (error) {
      console.error('[Storage] Error clearing storage:', error)
      return false
    }
  }

  /**
   * Get all keys in storage
   * @returns {string[]}
   */
  keys() {
    try {
      return Object.keys(this.storage)
    } catch (error) {
      console.error('[Storage] Error getting keys:', error)
      return []
    }
  }

  /**
   * Get storage size in bytes (approximate)
   * @returns {number}
   */
  size() {
    try {
      let total = 0
      for (let key in this.storage) {
        if (this.storage.hasOwnProperty(key)) {
          total += key.length + (this.storage.getItem(key)?.length || 0)
        }
      }
      return total
    } catch (error) {
      console.error('[Storage] Error calculating size:', error)
      return 0
    }
  }

  /**
   * Set item with expiration time
   * @param {string} key - Storage key
   * @param {*} value - Value to store
   * @param {number} ttl - Time to live in milliseconds
   * @returns {boolean} Success status
   */
  setWithExpiry(key, value, ttl) {
    const item = {
      value,
      expiry: Date.now() + ttl
    }
    return this.set(key, item)
  }

  /**
   * Get item with expiration check
   * @param {string} key - Storage key
   * @param {*} [defaultValue=null] - Default value if key doesn't exist or expired
   * @returns {*} Value or default
   */
  getWithExpiry(key, defaultValue = null) {
    const item = this.get(key)

    if (!item) {
      return defaultValue
    }

    // Check if item has expiry field
    if (item.expiry && item.value !== undefined) {
      if (Date.now() > item.expiry) {
        this.remove(key)
        return defaultValue
      }
      return item.value
    }

    // If no expiry, return as is
    return item
  }
}

// Create singleton instances
export const storage = new StorageService(localStorage)
export const sessionStorage = new StorageService(window.sessionStorage)

// Export class for testing or custom instances
export { StorageService }

// Export default instance
export default storage
