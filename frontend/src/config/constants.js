/**
 * Application Constants
 *
 * Centralized configuration for magic numbers and hard-coded values.
 * Makes it easy to update values and maintain consistency across the app.
 */

/**
 * API Configuration
 */
export const API_CONFIG = {
  // Base URL - can be overridden by environment variable
  BASE_URL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',

  // Request timeout in milliseconds (90 seconds)
  TIMEOUT: 90000,

  // Retry configuration
  MAX_RETRIES: 3,
  RETRY_DELAY: 1000, // milliseconds
}

/**
 * File Upload Configuration
 */
export const UPLOAD_CONFIG = {
  // Maximum file size: 50MB
  MAX_FILE_SIZE: 50 * 1024 * 1024,

  // Maximum files per upload
  MAX_FILES: 10,

  // Allowed file types
  ALLOWED_TYPES: [
    // Documents
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
    'text/markdown',

    // Spreadsheets
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',

    // Presentations
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',

    // Code files
    'text/javascript',
    'text/x-python',
    'application/json',
    'text/html',
    'text/css',
  ],

  // File extensions
  ALLOWED_EXTENSIONS: [
    '.pdf', '.doc', '.docx', '.txt', '.md',
    '.xls', '.xlsx', '.ppt', '.pptx',
    '.js', '.py', '.json', '.html', '.css',
    '.ts', '.jsx', '.tsx', '.vue'
  ]
}

/**
 * Chat Configuration
 */
export const CHAT_CONFIG = {
  // Maximum message length
  MAX_MESSAGE_LENGTH: 1000,

  // Title generation
  TITLE_MIN_LENGTH: 2,
  TITLE_MAX_LENGTH: 15,
  TITLE_PREFERRED_LENGTH: 8,

  // Chat history
  MAX_CHAT_HISTORY: 100,

  // Auto-save interval (milliseconds)
  AUTO_SAVE_INTERVAL: 5000,
}

/**
 * Voice Configuration
 */
export const VOICE_CONFIG = {
  // Audio recording settings
  SAMPLE_RATE: 16000,

  // Maximum recording duration (milliseconds)
  MAX_RECORDING_DURATION: 60000, // 1 minute

  // Audio format
  MIME_TYPE: 'audio/webm',
}

/**
 * UI Configuration
 */
export const UI_CONFIG = {
  // Animation durations (milliseconds)
  ANIMATION_FAST: 150,
  ANIMATION_NORMAL: 300,
  ANIMATION_SLOW: 500,

  // Notification duration
  NOTIFICATION_DURATION: 3000,

  // Debounce delays
  SEARCH_DEBOUNCE: 300,
  AUTO_SAVE_DEBOUNCE: 1000,

  // Pagination
  ITEMS_PER_PAGE: 20,
}

/**
 * Storage Keys
 */
export const STORAGE_KEYS = {
  // Authentication
  TOKEN: 'token',
  USER: 'user',

  // Settings
  THEME: 'dashboard-theme',
  API_CONFIG: 'api-configuration',

  // Data
  CHAT_HISTORY: 'chat-history',

  // Preferences
  SIDEBAR_COLLAPSED: 'sidebar-collapsed',
  LANGUAGE: 'language',
}

/**
 * Validation Rules
 */
export const VALIDATION = {
  // Username
  USERNAME_MIN_LENGTH: 3,
  USERNAME_MAX_LENGTH: 50,

  // Password
  PASSWORD_MIN_LENGTH: 6,
  PASSWORD_MAX_LENGTH: 100,

  // Email
  EMAIL_REGEX: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,

  // Verification code
  VERIFICATION_CODE_LENGTH: 6,
}

/**
 * HTTP Status Codes
 */
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  CONFLICT: 409,
  INTERNAL_SERVER_ERROR: 500,
  SERVICE_UNAVAILABLE: 503,
}

/**
 * Error Messages
 */
export const ERROR_MESSAGES = {
  // Network
  NETWORK_ERROR: 'Network error. Please check your connection.',
  TIMEOUT: 'Request timeout. Please try again.',

  // Authentication
  INVALID_CREDENTIALS: 'Invalid username or password.',
  SESSION_EXPIRED: 'Session expired. Please login again.',

  // File upload
  FILE_TOO_LARGE: `File size exceeds ${UPLOAD_CONFIG.MAX_FILE_SIZE / 1024 / 1024}MB limit.`,
  INVALID_FILE_TYPE: 'Invalid file type.',

  // Generic
  UNKNOWN_ERROR: 'An unknown error occurred.',
  SERVER_ERROR: 'Server error. Please try again later.',
}

/**
 * Success Messages
 */
export const SUCCESS_MESSAGES = {
  LOGIN_SUCCESS: 'Login successful!',
  REGISTER_SUCCESS: 'Registration successful!',
  SAVE_SUCCESS: 'Saved successfully!',
  DELETE_SUCCESS: 'Deleted successfully!',
  UPLOAD_SUCCESS: 'Upload successful!',
}

export default {
  API_CONFIG,
  UPLOAD_CONFIG,
  CHAT_CONFIG,
  VOICE_CONFIG,
  UI_CONFIG,
  STORAGE_KEYS,
  VALIDATION,
  HTTP_STATUS,
  ERROR_MESSAGES,
  SUCCESS_MESSAGES,
}
