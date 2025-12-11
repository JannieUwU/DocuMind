/**
 * API Response Types
 *
 * Type definitions for API requests and responses.
 * Can be imported in both .ts and .js files (with JSDoc).
 */

/**
 * Generic API Response
 * @template T - The type of data in the response
 */
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  detail?: string
  error?: string
}

/**
 * Paginated Response
 * @template T - The type of items in the list
 */
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  hasMore: boolean
}

/**
 * Error Response
 */
export interface ErrorResponse {
  success: false
  error: string
  detail?: string
  code?: string
  statusCode?: number
}

// ===== Authentication Types =====

/**
 * Login Request
 */
export interface LoginRequest {
  username: string
  password: string
}

/**
 * Login Response
 */
export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in?: number
}

/**
 * Register Request
 */
export interface RegisterRequest {
  username: string
  email: string
  password: string
  verification_code: string
}

/**
 * User Info
 */
export interface UserInfo {
  id: string | number
  username: string
  email: string
  created_at?: string
  updated_at?: string
}

/**
 * Reset Password Request
 */
export interface ResetPasswordRequest {
  email: string
  verification_code: string
  new_password: string
}

/**
 * Send Verification Code Request
 */
export interface SendCodeRequest {
  email: string
}

// ===== Chat Types =====

/**
 * Chat Message Role
 */
export type MessageRole = 'user' | 'assistant' | 'system'

/**
 * Chat Message
 */
export interface ChatMessage {
  id?: string | number
  role: MessageRole
  content: string
  timestamp: string | Date
  isError?: boolean
  isStreaming?: boolean
  isComplete?: boolean  // 标记消息是否已Done生成（false时不显示工具按钮）
  metadata?: Record<string, any>
}

/**
 * Chat Conversation
 */
export interface ChatConversation {
  id: string | number
  title: string
  messages: ChatMessage[]
  created_at?: string
  updated_at?: string
  isGeneratingTitle?: boolean
}

/**
 * Chat Query Request
 */
export interface ChatQueryRequest {
  message: string
  conversation_id?: string | number
  stream?: boolean
  response_quality?: 'Fast' | 'Standard' | 'High'
}

/**
 * Chat Query Response
 */
export interface ChatQueryResponse {
  response: string
  conversation_id?: string | number
  sources?: string[]
  metadata?: {
    model?: string
    tokens_used?: number
    duration?: number
  }
}

// ===== Document Types =====

/**
 * Document Upload Request
 */
export interface DocumentUploadRequest {
  file: File
  conversation_id?: string | number
}

/**
 * Document Info
 */
export interface DocumentInfo {
  id: string | number
  filename: string
  size: number
  mime_type: string
  conversation_id?: string | number
  uploaded_at: string
  status: 'uploading' | 'processing' | 'ready' | 'error'
  error_message?: string
}

/**
 * Document List Response
 */
export interface DocumentListResponse {
  documents: DocumentInfo[]
  total: number
}

// ===== Configuration Types =====

/**
 * API Configuration
 */
export interface ApiConfiguration {
  apiKey?: string
  openaiApiKey?: string
  anthropicApiKey?: string
  cohereApiKey?: string
  rerankerKey?: string
  baseUrl?: string
  rerankerBaseUrl?: string
  databaseUrl?: string
  model?: string
}

/**
 * Configuration Test Result
 */
export interface ConfigTestResult {
  success: boolean
  message?: string
  errors?: string[]
}

// ===== Voice Types =====

/**
 * Voice Transcription Request
 */
export interface TranscribeRequest {
  audio: Blob
  language?: string
}

/**
 * Voice Transcription Response
 */
export interface TranscribeResponse {
  text: string
  language?: string
  confidence?: number
}

// ===== Instruction Assistant Types =====

/**
 * Instruction Optimization Mode
 */
export type OptimizationMode = 'scene' | 'analysis' | 'intelligent'

/**
 * Instruction Optimization Request
 */
export interface OptimizeInstructionRequest {
  instruction: string
  mode: OptimizationMode
}

/**
 * Instruction Optimization Response
 */
export interface OptimizeInstructionResponse {
  optimized_instruction: string
  suggestions?: string[]
  improvements?: string[]
}

// ===== File Upload Types =====

/**
 * File Upload Progress
 */
export interface UploadProgress {
  filename: string
  progress: number
  status: 'uploading' | 'processing' | 'completed' | 'error'
  error?: string
}

/**
 * File Upload Result
 */
export interface UploadResult {
  success: boolean
  filename: string
  document_id?: string | number
  error?: string
}

// ===== Storage Types =====

/**
 * Storage Item with Expiry
 */
export interface StorageItem<T> {
  value: T
  expiry: number
}

// ===== Validation Types =====

/**
 * Form Validation Result
 */
export interface ValidationResult {
  valid: boolean
  errors?: Record<string, string>
}

/**
 * Field Validation Rule
 */
export interface ValidationRule {
  required?: boolean
  minLength?: number
  maxLength?: number
  pattern?: RegExp
  custom?: (value: any) => boolean | string
}

// ===== UI Types =====

/**
 * Notification Type
 */
export type NotificationType = 'info' | 'success' | 'warning' | 'error'

/**
 * Notification Options
 */
export interface NotificationOptions {
  message: string
  type?: NotificationType
  duration?: number
  id?: string
}

/**
 * Theme Type
 */
export type ThemeType = 'light' | 'dark'

// ===== Utility Types =====

/**
 * Async State
 */
export interface AsyncState<T, E = Error> {
  data: T | null
  loading: boolean
  error: E | null
}

/**
 * Action Result
 */
export interface ActionResult<T = any> {
  success: boolean
  data?: T
  error?: string
}

// ===== Export all types =====
export type {
  // Re-export for convenience
  ApiResponse,
  PaginatedResponse,
  ErrorResponse,
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  UserInfo,
  ResetPasswordRequest,
  SendCodeRequest,
  MessageRole,
  ChatMessage,
  ChatConversation,
  ChatQueryRequest,
  ChatQueryResponse,
  DocumentUploadRequest,
  DocumentInfo,
  DocumentListResponse,
  ApiConfiguration,
  ConfigTestResult,
  TranscribeRequest,
  TranscribeResponse,
  OptimizationMode,
  OptimizeInstructionRequest,
  OptimizeInstructionResponse,
  UploadProgress,
  UploadResult,
  StorageItem,
  ValidationResult,
  ValidationRule,
  NotificationType,
  NotificationOptions,
  ThemeType,
  AsyncState,
  ActionResult,
}
