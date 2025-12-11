/**
 * API Endpoints Configuration
 *
 * Centralized definition of all API endpoints.
 * Makes it easy to update endpoints and maintain consistency.
 */

import { API_CONFIG } from './constants'

/**
 * Helper function to build full URL
 * @param {string} endpoint - Relative endpoint path
 * @returns {string} Full URL
 */
export const buildUrl = (endpoint) => {
  // Remove leading slash if present to avoid double slashes
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint
  return `${API_CONFIG.BASE_URL}/${cleanEndpoint}`
}

/**
 * Authentication Endpoints
 */
export const AUTH_ENDPOINTS = {
  LOGIN: '/auth/login',
  REGISTER: '/auth/register',
  LOGOUT: '/auth/logout',
  ME: '/auth/me',
  SEND_CODE: '/auth/send-code',
  RESET_PASSWORD: '/auth/reset-password',
  REFRESH_TOKEN: '/auth/refresh',
}

/**
 * Document Endpoints
 */
export const DOCUMENT_ENDPOINTS = {
  UPLOAD: '/documents/upload',
  LIST: '/documents/list',
  DELETE: '/documents/delete',
  GET: (id) => `/documents/${id}`,
  DOWNLOAD: (id) => `/documents/${id}/download`,
}

/**
 * Chat Endpoints
 */
export const CHAT_ENDPOINTS = {
  MESSAGE: '/chat/message',
  QUERY: '/chat/query',
  STREAM: '/chat/stream',
  CONVERSATIONS: '/chat/conversations',
  CONVERSATION: (id) => `/chat/conversations/${id}`,
  MESSAGES: (conversationId) => `/chat/conversations/${conversationId}/messages`,
  DELETE_CONVERSATION: (id) => `/chat/conversations/${id}`,
}

/**
 * Voice Endpoints
 */
export const VOICE_ENDPOINTS = {
  TRANSCRIBE: '/voice/transcribe',
  TEXT_TO_SPEECH: '/voice/tts',
}

/**
 * Configuration Endpoints
 */
export const CONFIG_ENDPOINTS = {
  GET: '/config',
  UPDATE: '/config',
  TEST: '/config/test',
}

/**
 * Instruction Assistant Endpoints
 */
export const INSTRUCTION_ENDPOINTS = {
  OPTIMIZE: '/instruction/optimize',
  ANALYZE: '/instruction/analyze',
}

/**
 * User Endpoints
 */
export const USER_ENDPOINTS = {
  PROFILE: '/user/profile',
  UPDATE_PROFILE: '/user/profile',
  CHANGE_PASSWORD: '/user/password',
  PREFERENCES: '/user/preferences',
}

/**
 * All endpoints grouped
 */
export const ENDPOINTS = {
  AUTH: AUTH_ENDPOINTS,
  DOCUMENT: DOCUMENT_ENDPOINTS,
  CHAT: CHAT_ENDPOINTS,
  VOICE: VOICE_ENDPOINTS,
  CONFIG: CONFIG_ENDPOINTS,
  INSTRUCTION: INSTRUCTION_ENDPOINTS,
  USER: USER_ENDPOINTS,
}

/**
 * Full URL builders for common endpoints
 */
export const API_URLS = {
  // Auth
  login: () => buildUrl(AUTH_ENDPOINTS.LOGIN),
  register: () => buildUrl(AUTH_ENDPOINTS.REGISTER),
  me: () => buildUrl(AUTH_ENDPOINTS.ME),

  // Documents
  uploadDocument: (conversationId) =>
    `${buildUrl(DOCUMENT_ENDPOINTS.UPLOAD)}${conversationId ? `?conversation_id=${conversationId}` : ''}`,
  listDocuments: () => buildUrl(DOCUMENT_ENDPOINTS.LIST),

  // Chat
  chatMessage: () => buildUrl(CHAT_ENDPOINTS.MESSAGE),
  chatQuery: () => buildUrl(CHAT_ENDPOINTS.QUERY),
  chatStream: () => buildUrl(CHAT_ENDPOINTS.STREAM),
  updateConversation: (id) => buildUrl(CHAT_ENDPOINTS.CONVERSATION(id)),

  // Voice
  transcribeAudio: () => buildUrl(VOICE_ENDPOINTS.TRANSCRIBE),

  // Instruction
  optimizeInstruction: () => buildUrl(INSTRUCTION_ENDPOINTS.OPTIMIZE),

  // Config
  saveConfig: () => buildUrl(CONFIG_ENDPOINTS.UPDATE),
  testConfig: () => buildUrl(CONFIG_ENDPOINTS.TEST),
}

export default {
  ENDPOINTS,
  API_URLS,
  buildUrl,
}
