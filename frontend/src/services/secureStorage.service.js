/**
 * Secure Storage Service
 *
 * Provides encrypted storage for sensitive data like authentication tokens.
 * Uses Web Crypto API (built-in, no external dependencies) for AES-GCM encryption.
 *
 * Features:
 * - AES-256-GCM encryption
 * - Unique encryption key per browser/device
 * - Protection against XSS token theft
 * - Automatic key generation and storage
 * - Type-safe operations
 *
 * Security Notes:
 * - Encryption key is stored in localStorage (same origin as encrypted data)
 * - This protects against casual token theft but not sophisticated XSS attacks
 * - For maximum security, use httpOnly cookies (requires backend support)
 * - This is defense-in-depth: adds a layer of protection
 */

import { ErrorHandler } from '@/utils/errorHandler'

class SecureStorageService {
  constructor() {
    this.keyName = '__secure_storage_key__'
    this.algorithm = 'AES-GCM'
    this.keyLength = 256
    this.ivLength = 12 // 96 bits for AES-GCM
    this.cryptoKey = null
  }

  /**
   * Initialize the encryption key
   * Generates a new key if one doesn't exist
   * @private
   */
  async initKey() {
    if (this.cryptoKey) {
      return this.cryptoKey
    }

    try {
      // Try to load existing key from localStorage
      const storedKey = localStorage.getItem(this.keyName)

      if (storedKey) {
        // Import stored key
        const keyData = this.base64ToArrayBuffer(storedKey)
        this.cryptoKey = await window.crypto.subtle.importKey(
          'raw',
          keyData,
          { name: this.algorithm, length: this.keyLength },
          true, // extractable
          ['encrypt', 'decrypt']
        )
      } else {
        // Generate new key
        this.cryptoKey = await window.crypto.subtle.generateKey(
          { name: this.algorithm, length: this.keyLength },
          true, // extractable
          ['encrypt', 'decrypt']
        )

        // Export and store the key
        const exportedKey = await window.crypto.subtle.exportKey('raw', this.cryptoKey)
        const keyBase64 = this.arrayBufferToBase64(exportedKey)
        localStorage.setItem(this.keyName, keyBase64)
      }

      return this.cryptoKey
    } catch (error) {
      ErrorHandler.logError(error, 'SecureStorage.initKey')
      throw new Error('Failed to initialize encryption key')
    }
  }

  /**
   * Encrypt data using AES-GCM
   * @private
   * @param {string} data - Data to encrypt
   * @returns {Promise<string>} Base64-encoded encrypted data with IV
   */
  async encrypt(data) {
    try {
      const key = await this.initKey()

      // Generate random IV (Initialization Vector)
      const iv = window.crypto.getRandomValues(new Uint8Array(this.ivLength))

      // Convert data to ArrayBuffer
      const encoder = new TextEncoder()
      const dataBuffer = encoder.encode(data)

      // Encrypt
      const encryptedBuffer = await window.crypto.subtle.encrypt(
        { name: this.algorithm, iv },
        key,
        dataBuffer
      )

      // Combine IV + encrypted data
      const combined = new Uint8Array(iv.length + encryptedBuffer.byteLength)
      combined.set(iv, 0)
      combined.set(new Uint8Array(encryptedBuffer), iv.length)

      // Convert to base64
      return this.arrayBufferToBase64(combined.buffer)
    } catch (error) {
      ErrorHandler.logError(error, 'SecureStorage.encrypt')
      throw new Error('Encryption failed')
    }
  }

  /**
   * Decrypt data using AES-GCM
   * @private
   * @param {string} encryptedData - Base64-encoded encrypted data with IV
   * @returns {Promise<string>} Decrypted data
   */
  async decrypt(encryptedData) {
    try {
      const key = await this.initKey()

      // Decode from base64
      const combined = this.base64ToArrayBuffer(encryptedData)

      // Extract IV and encrypted data
      const iv = combined.slice(0, this.ivLength)
      const encryptedBuffer = combined.slice(this.ivLength)

      // Decrypt
      const decryptedBuffer = await window.crypto.subtle.decrypt(
        { name: this.algorithm, iv },
        key,
        encryptedBuffer
      )

      // Convert back to string
      const decoder = new TextDecoder()
      return decoder.decode(decryptedBuffer)
    } catch (error) {
      ErrorHandler.logError(error, 'SecureStorage.decrypt')
      throw new Error('Decryption failed')
    }
  }

  /**
   * Store encrypted data
   * @param {string} key - Storage key
   * @param {any} value - Value to store (will be JSON stringified)
   * @returns {Promise<boolean>} Success status
   */
  async setSecure(key, value) {
    try {
      // Serialize value
      const serialized = typeof value === 'string'
        ? value
        : JSON.stringify(value)

      // Encrypt
      const encrypted = await this.encrypt(serialized)

      // Store with prefix to identify encrypted data
      localStorage.setItem(`__secure__${key}`, encrypted)

      return true
    } catch (error) {
      ErrorHandler.logError(error, `SecureStorage.setSecure(${key})`)
      return false
    }
  }

  /**
   * Retrieve and decrypt data
   * @template T
   * @param {string} key - Storage key
   * @param {T} [defaultValue=null] - Default value if key doesn't exist
   * @returns {Promise<T|null>} Decrypted value or default
   */
  async getSecure(key, defaultValue = null) {
    try {
      const encrypted = localStorage.getItem(`__secure__${key}`)

      if (!encrypted) {
        return defaultValue
      }

      // Decrypt
      const decrypted = await this.decrypt(encrypted)

      // Parse if JSON
      try {
        return JSON.parse(decrypted)
      } catch {
        return decrypted
      }
    } catch (error) {
      ErrorHandler.logError(error, `SecureStorage.getSecure(${key})`)
      return defaultValue
    }
  }

  /**
   * Remove encrypted data
   * @param {string} key - Storage key
   * @returns {boolean} Success status
   */
  removeSecure(key) {
    try {
      localStorage.removeItem(`__secure__${key}`)
      return true
    } catch (error) {
      ErrorHandler.logError(error, `SecureStorage.removeSecure(${key})`)
      return false
    }
  }

  /**
   * Check if encrypted key exists
   * @param {string} key - Storage key
   * @returns {boolean}
   */
  hasSecure(key) {
    try {
      return localStorage.getItem(`__secure__${key}`) !== null
    } catch (error) {
      ErrorHandler.logError(error, `SecureStorage.hasSecure(${key})`)
      return false
    }
  }

  /**
   * Migrate plain data to encrypted storage
   * @param {string} key - Storage key
   * @returns {Promise<boolean>} Success status
   */
  async migrateToSecure(key) {
    try {
      // Get plain data
      const plainData = localStorage.getItem(key)

      if (!plainData) {
        return false
      }

      // Store encrypted
      await this.setSecure(key, plainData)

      // Remove plain data
      localStorage.removeItem(key)

      return true
    } catch (error) {
      ErrorHandler.logError(error, `SecureStorage.migrateToSecure(${key})`)
      return false
    }
  }

  /**
   * Clear all encrypted data
   * @returns {number} Number of items cleared
   */
  clearSecure() {
    try {
      let count = 0
      const keys = Object.keys(localStorage)

      for (const key of keys) {
        if (key.startsWith('__secure__')) {
          localStorage.removeItem(key)
          count++
        }
      }

      return count
    } catch (error) {
      ErrorHandler.logError(error, 'SecureStorage.clearSecure')
      return 0
    }
  }

  /**
   * Rotate encryption key (re-encrypt all data with new key)
   * @returns {Promise<boolean>} Success status
   */
  async rotateKey() {
    try {
      // Get all encrypted keys
      const keys = Object.keys(localStorage)
        .filter(k => k.startsWith('__secure__'))
        .map(k => k.replace('__secure__', ''))

      // Decrypt all data with old key
      const decryptedData = {}
      for (const key of keys) {
        decryptedData[key] = await this.getSecure(key)
      }

      // Remove old key
      localStorage.removeItem(this.keyName)
      this.cryptoKey = null

      // Generate new key
      await this.initKey()

      // Re-encrypt all data with new key
      for (const key of keys) {
        await this.setSecure(key, decryptedData[key])
      }

      return true
    } catch (error) {
      ErrorHandler.logError(error, 'SecureStorage.rotateKey')
      return false
    }
  }

  /**
   * Convert ArrayBuffer to Base64
   * @private
   */
  arrayBufferToBase64(buffer) {
    const bytes = new Uint8Array(buffer)
    let binary = ''
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i])
    }
    return window.btoa(binary)
  }

  /**
   * Convert Base64 to ArrayBuffer
   * @private
   */
  base64ToArrayBuffer(base64) {
    const binary = window.atob(base64)
    const bytes = new Uint8Array(binary.length)
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i)
    }
    return bytes.buffer
  }
}

// Export singleton instance
export const secureStorage = new SecureStorageService()

// Export class for testing
export { SecureStorageService }

export default secureStorage
