/**
 * Authentication Store
 *
 * Manages user authentication state and operations.
 * @typedef {import('@/types/api.types').UserInfo} UserInfo
 * @typedef {import('@/types/api.types').LoginRequest} LoginRequest
 * @typedef {import('@/types/api.types').ActionResult} ActionResult
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/utils/api'
import storage from '@/services/storage.service'
import secureStorage from '@/services/secureStorage.service'
import { ErrorHandler, ValidationError } from '@/utils/errorHandler'
import { formValidators, validators } from '@/utils/validators'

export const useAuthStore = defineStore('auth', () => {
  /** @type {import('vue').Ref<UserInfo | null>} */
  const user = ref(null)

  /** @type {import('vue').Ref<boolean>} */
  const isAuthenticated = ref(false)

  const userDisplayName = computed(() => user.value?.username || 'Guest')
  const userEmail = computed(() => user.value?.email || '')

  async function initAuth() {
    // Try secure storage first
    let storedToken = await secureStorage.getSecure('token')

    // Fallback to plain storage for migration
    if (!storedToken) {
      storedToken = storage.get('token')

      // Migrate to secure storage if found in plain storage
      if (storedToken) {
        await secureStorage.setSecure('token', storedToken)
        storage.remove('token')
      }
    }

    const storedUser = storage.get('user')

    if (storedToken && storedToken.startsWith('mock-token-')) {
      console.log('Clearing old mock token')
      secureStorage.removeSecure('token')
      storage.remove('token')
      storage.remove('user')
      return
    }

    if (storedToken && storedUser) {
      try {
        const response = await api.get('/auth/me')
        if (response.data) {
          isAuthenticated.value = true
          user.value = response.data
          storage.set('user', response.data)
        }
      } catch (error) {
        console.log('Token expired or invalid, clearing')
        secureStorage.removeSecure('token')
        storage.remove('token')
        storage.remove('user')
        isAuthenticated.value = false
        user.value = null
      }
    }
  }

  /**
   * Login user
   * @param {string} username - Username
   * @param {string} password - Password
   * @returns {Promise<ActionResult>} Login result
   */
  async function login(username, password) {
    if (!username.trim() || !password.trim()) {
      throw new ValidationError('Username和Password不能为空')
    }

    try {
      const response = await api.post('/auth/login', {
        username: username.trim(),
        password: password.trim()
      })

      if (response.data && response.data.access_token) {
        const token = response.data.access_token

        // Store token in encrypted storage
        await secureStorage.setSecure('token', token)

        const userResponse = await api.get('/auth/me')
        const userInfo = userResponse.data

        isAuthenticated.value = true
        user.value = userInfo
        storage.set('user', userInfo)

        return { success: true }
      } else {
        return { success: false, error: 'LoginFailed' }
      }
    } catch (error) {
      const appError = ErrorHandler.handleApiError(error)
      ErrorHandler.logError(appError, 'AuthStore.login')

      return {
        success: false,
        error: ErrorHandler.getUserMessage(appError)
      }
    }
  }

  /**
   * Send verification code to email
   * @param {string} email - Email address
   * @returns {Promise<ActionResult>} Send result
   */
  async function sendVerificationCode(email) {
    const emailValidation = validators.email(email)
    if (!emailValidation.valid) {
      return { success: false, error: emailValidation.message }
    }

    try {
      const response = await api.post('/auth/send-code', {
        email: email.trim()
      })

      if (response.data && response.data.success) {
        return { success: true }
      } else {
        return { success: false, error: response.data?.message || 'Failed to send verification code' }
      }
    } catch (error) {
      const appError = ErrorHandler.handleApiError(error)
      ErrorHandler.logError(appError, 'AuthStore.sendVerificationCode')

      return {
        success: false,
        error: ErrorHandler.getUserMessage(appError)
      }
    }
  }

  /**
   * Register new user
   * @param {string} username
   * @param {string} email
   * @param {string} password
   * @param {string} verificationCode
   * @returns {Promise<ActionResult>}
   */
  async function register(username, email, password, verificationCode) {
    // Validate form using composite validator
    const validation = formValidators.register({
      username,
      email,
      password,
      confirmPassword: password, // Not used in API call, just for validation
      verificationCode
    })

    if (!validation.valid) {
      // Return first error
      const firstError = Object.values(validation.errors)[0]
      return { success: false, error: firstError }
    }

    try {
      const response = await api.post('/auth/register', {
        username: username.trim(),
        email: email.trim(),
        password: password.trim(),
        verification_code: verificationCode.trim()
      })

      if (response.data && response.data.success) {
        return { success: true }
      } else {
        return { success: false, error: response.data?.message || 'Registration failed' }
      }
    } catch (error) {
      const appError = ErrorHandler.handleApiError(error)
      ErrorHandler.logError(appError, 'AuthStore.register')

      return {
        success: false,
        error: ErrorHandler.getUserMessage(appError)
      }
    }
  }

  /**
   * Reset password
   * @param {string} email
   * @param {string} verificationCode
   * @param {string} newPassword
   * @returns {Promise<ActionResult>}
   */
  async function resetPassword(email, verificationCode, newPassword) {
    // Validate form using composite validator
    const validation = formValidators.resetPassword({
      email,
      verificationCode,
      newPassword,
      confirmPassword: newPassword // Not used in API call, just for validation
    })

    if (!validation.valid) {
      const firstError = Object.values(validation.errors)[0]
      return { success: false, error: firstError }
    }

    try {
      const response = await api.post('/auth/reset-password', {
        email: email.trim(),
        verification_code: verificationCode.trim(),
        new_password: newPassword.trim()
      })

      if (response.data && response.data.success) {
        return { success: true }
      } else {
        return { success: false, error: response.data?.message || 'Password reset failed' }
      }
    } catch (error) {
      const appError = ErrorHandler.handleApiError(error)
      ErrorHandler.logError(appError, 'AuthStore.resetPassword')

      return {
        success: false,
        error: ErrorHandler.getUserMessage(appError)
      }
    }
  }

  function logout() {
    isAuthenticated.value = false
    user.value = null
    secureStorage.removeSecure('token')
    storage.remove('token') // Remove legacy token if exists
    storage.remove('user')
  }

  return {
    user,
    isAuthenticated,
    userDisplayName,
    userEmail,
    initAuth,
    login,
    sendVerificationCode,
    register,
    resetPassword,
    logout
  }
})