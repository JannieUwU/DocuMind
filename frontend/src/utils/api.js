import axios from 'axios'
import storage from '@/services/storage.service'
import secureStorage from '@/services/secureStorage.service'
import { API_CONFIG } from '@/config/constants'
import { AUTH_ENDPOINTS, CONFIG_ENDPOINTS } from '@/config/endpoints'
import { ErrorHandler } from '@/utils/errorHandler'

const api = axios.create({
  baseURL: API_CONFIG.BASE_URL,
  timeout: API_CONFIG.TIMEOUT
})

// 请求拦截器
api.interceptors.request.use(
  async (config) => {
    // Try to get token from secure storage first, then fallback to legacy
    let token = await secureStorage.getSecure('token')
    if (!token) {
      token = storage.get('token')
    }

    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    ErrorHandler.logError(error, 'API Request')
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    const appError = ErrorHandler.handleApiError(error)

    // Handle authentication errors
    if (ErrorHandler.requiresAuth(appError)) {
      const url = error.config?.url || ''
      const excludedPaths = [
        AUTH_ENDPOINTS.LOGIN,
        AUTH_ENDPOINTS.REGISTER,
        AUTH_ENDPOINTS.SEND_CODE,
        CONFIG_ENDPOINTS.GET
      ]
      const shouldRedirect = !excludedPaths.some(path => url.includes(path))

      if (shouldRedirect) {
        // Clear both secure and legacy tokens
        secureStorage.removeSecure('token')
        storage.remove('token')
        storage.remove('user')
        window.location.href = '/#/login'
      }
    }

    // Log error for monitoring
    ErrorHandler.logError(appError, 'API Response')

    return Promise.reject(appError)
  }
)

export { api }