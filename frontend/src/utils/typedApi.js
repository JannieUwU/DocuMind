/**
 * Type-Safe API Client
 *
 * Enhanced API client with TypeScript-like type safety using JSDoc.
 * Can be used in both .js and .ts files.
 */

import axios from 'axios'
import storage from '@/services/storage.service'
import { API_CONFIG } from '@/config/constants'
import { AUTH_ENDPOINTS, CONFIG_ENDPOINTS } from '@/config/endpoints'

/**
 * @typedef {import('@/types/api.types').ApiResponse} ApiResponse
 * @typedef {import('@/types/api.types').LoginRequest} LoginRequest
 * @typedef {import('@/types/api.types').LoginResponse} LoginResponse
 * @typedef {import('@/types/api.types').RegisterRequest} RegisterRequest
 * @typedef {import('@/types/api.types').UserInfo} UserInfo
 * @typedef {import('@/types/api.types').ChatQueryRequest} ChatQueryRequest
 * @typedef {import('@/types/api.types').ChatQueryResponse} ChatQueryResponse
 * @typedef {import('@/types/api.types').ApiConfiguration} ApiConfiguration
 */

const api = axios.create({
  baseURL: API_CONFIG.BASE_URL,
  timeout: API_CONFIG.TIMEOUT
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = storage.get('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (error.response?.status === 401) {
      const url = error.config?.url || ''
      const excludedPaths = [
        AUTH_ENDPOINTS.LOGIN,
        AUTH_ENDPOINTS.REGISTER,
        AUTH_ENDPOINTS.SEND_CODE,
        CONFIG_ENDPOINTS.GET
      ]
      const shouldRedirect = !excludedPaths.some(path => url.includes(path))

      if (shouldRedirect) {
        storage.remove('token')
        storage.remove('user')
        window.location.href = '/#/login'
      }
    }
    return Promise.reject(error)
  }
)

/**
 * Type-safe API methods with JSDoc
 */
class TypedApiClient {
  /**
   * Login user
   * @param {LoginRequest} credentials - Login credentials
   * @returns {Promise<ApiResponse<LoginResponse>>}
   */
  async login(credentials) {
    const response = await api.post(AUTH_ENDPOINTS.LOGIN, credentials)
    return response.data
  }

  /**
   * Register user
   * @param {RegisterRequest} data - Registration data
   * @returns {Promise<ApiResponse<{success: boolean}>>}
   */
  async register(data) {
    const response = await api.post(AUTH_ENDPOINTS.REGISTER, data)
    return response.data
  }

  /**
   * Get current user info
   * @returns {Promise<ApiResponse<UserInfo>>}
   */
  async getCurrentUser() {
    const response = await api.get(AUTH_ENDPOINTS.ME)
    return response.data
  }

  /**
   * Send chat query
   * @param {ChatQueryRequest} request - Chat query request
   * @returns {Promise<ApiResponse<ChatQueryResponse>>}
   */
  async sendChatQuery(request) {
    const response = await api.post('/chat/query', request)
    return response.data
  }

  /**
   * Update configuration
   * @param {ApiConfiguration} config - API configuration
   * @returns {Promise<ApiResponse<{success: boolean}>>}
   */
  async updateConfig(config) {
    const response = await api.post(CONFIG_ENDPOINTS.UPDATE, config)
    return response.data
  }

  /**
   * Upload document
   * @param {FormData} formData - Form data with file
   * @param {string|number} [conversationId] - Optional conversation ID
   * @returns {Promise<ApiResponse<{document_id: string}>>}
   */
  async uploadDocument(formData, conversationId) {
    const url = conversationId
      ? `/documents/upload?conversation_id=${conversationId}`
      : '/documents/upload'
    const response = await api.post(url, formData)
    return response.data
  }
}

// Export singleton instance
export const typedApi = new TypedApiClient()

// Export base axios instance for backward compatibility
export { api }
