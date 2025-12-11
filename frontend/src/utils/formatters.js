/**
 * Formatting Utilities
 *
 * Centralized formatting logic to avoid duplication.
 */

/**
 * Format date to readable string
 * @param {string | Date} date - Date to format
 * @param {Object} [options] - Format options
 * @param {boolean} [options.includeTime=true] - Include time
 * @param {boolean} [options.relative=false] - Use relative time (e.g., "2 hours ago")
 * @returns {string}
 */
export function formatDate(date, options = {}) {
  const { includeTime = true, relative = false } = options

  const dateObj = date instanceof Date ? date : new Date(date)

  if (isNaN(dateObj.getTime())) {
    return 'Invalid date'
  }

  if (relative) {
    return formatRelativeTime(dateObj)
  }

  const dateStr = dateObj.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })

  if (!includeTime) {
    return dateStr
  }

  const timeStr = dateObj.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })

  return `${dateStr} ${timeStr}`
}

/**
 * Format relative time (e.g., "2 hours ago")
 * @param {string | Date} date - Date to format
 * @returns {string}
 */
export function formatRelativeTime(date) {
  const dateObj = date instanceof Date ? date : new Date(date)
  const now = new Date()
  const diffMs = now - dateObj
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)
  const diffHour = Math.floor(diffMin / 60)
  const diffDay = Math.floor(diffHour / 24)

  if (diffSec < 60) {
    return 'Just now'
  } else if (diffMin < 60) {
    return `${diffMin}minutes ago`
  } else if (diffHour < 24) {
    return `${diffHour}hours ago`
  } else if (diffDay < 7) {
    return `${diffDay}days ago`
  } else {
    return formatDate(dateObj, { includeTime: false })
  }
}

/**
 * Format file size to human readable string
 * @param {number} bytes - File size in bytes
 * @param {number} [decimals=2] - Number of decimal places
 * @returns {string}
 */
export function formatFileSize(bytes, decimals = 2) {
  if (bytes === 0) return '0 Bytes'

  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return parseFloat((bytes / Math.pow(k, i)).toFixed(decimals)) + ' ' + sizes[i]
}

/**
 * Format number with thousands separator
 * @param {number} num - Number to format
 * @returns {string}
 */
export function formatNumber(num) {
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

/**
 * Format percentage
 * @param {number} value - Value (0-1 or 0-100)
 * @param {Object} [options] - Format options
 * @param {boolean} [options.multiply=false] - Multiply by 100 if value is 0-1
 * @param {number} [options.decimals=1] - Number of decimal places
 * @returns {string}
 */
export function formatPercentage(value, options = {}) {
  const { multiply = false, decimals = 1 } = options
  const num = multiply ? value * 100 : value
  return `${num.toFixed(decimals)}%`
}

/**
 * Format duration in milliseconds to readable string
 * @param {number} ms - Duration in milliseconds
 * @returns {string}
 */
export function formatDuration(ms) {
  const seconds = Math.floor(ms / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)

  if (hours > 0) {
    return `${hours}h ${minutes % 60}m`
  } else if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`
  } else {
    return `${seconds}s`
  }
}

/**
 * Truncate string with ellipsis
 * @param {string} str - String to truncate
 * @param {number} maxLength - Maximum length
 * @param {string} [suffix='...'] - Suffix to add
 * @returns {string}
 */
export function truncate(str, maxLength, suffix = '...') {
  if (!str || str.length <= maxLength) {
    return str
  }
  return str.substring(0, maxLength - suffix.length) + suffix
}

/**
 * Capitalize first letter of string
 * @param {string} str - String to capitalize
 * @returns {string}
 */
export function capitalize(str) {
  if (!str) return ''
  return str.charAt(0).toUpperCase() + str.slice(1)
}

/**
 * Convert string to title case
 * @param {string} str - String to convert
 * @returns {string}
 */
export function titleCase(str) {
  if (!str) return ''
  return str
    .toLowerCase()
    .split(' ')
    .map(word => capitalize(word))
    .join(' ')
}

/**
 * Format markdown text (remove markdown syntax)
 * @param {string} text - Markdown text
 * @returns {string}
 */
export function stripMarkdown(text) {
  if (!text) return ''

  return text
    // Remove headers
    .replace(/^#{1,6}\s+/gm, '')
    // Remove bold/italic
    .replace(/(\*\*|__)(.*?)\1/g, '$2')
    .replace(/(\*|_)(.*?)\1/g, '$2')
    // Remove links
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    // Remove code blocks
    .replace(/```[\s\S]*?```/g, '')
    .replace(/`([^`]+)`/g, '$1')
    // Remove images
    .replace(/!\[([^\]]*)\]\([^)]+\)/g, '')
    // Remove blockquotes
    .replace(/^>\s+/gm, '')
    // Remove lists
    .replace(/^\s*[-*+]\s+/gm, '')
    .replace(/^\s*\d+\.\s+/gm, '')
    .trim()
}

/**
 * Format chat message content
 * Clean up and format message text
 * @param {string} content - Message content
 * @param {Object} [options] - Format options
 * @param {boolean} [options.preserveNewlines=true] - Preserve newlines
 * @param {number} [options.maxLength] - Maximum length (truncate if longer)
 * @returns {string}
 */
export function formatMessageContent(content, options = {}) {
  const { preserveNewlines = true, maxLength } = options

  if (!content) return ''

  let formatted = content.trim()

  // Normalize line breaks
  if (!preserveNewlines) {
    formatted = formatted.replace(/\n+/g, ' ')
  }

  // Remove extra whitespace
  formatted = formatted.replace(/\s+/g, ' ')

  // Truncate if needed
  if (maxLength && formatted.length > maxLength) {
    formatted = truncate(formatted, maxLength)
  }

  return formatted
}

/**
 * Extract preview text from content
 * @param {string} content - Full content
 * @param {number} [maxLength=100] - Maximum preview length
 * @returns {string}
 */
export function getPreviewText(content, maxLength = 100) {
  const stripped = stripMarkdown(content)
  const cleaned = formatMessageContent(stripped, { preserveNewlines: false })
  return truncate(cleaned, maxLength)
}

/**
 * Format API key for display (hide middle part)
 * @param {string} apiKey - API key
 * @param {number} [visibleChars=4] - Number of visible characters at start and end
 * @returns {string}
 */
export function formatApiKey(apiKey, visibleChars = 4) {
  if (!apiKey || apiKey.length <= visibleChars * 2) {
    return apiKey
  }

  const start = apiKey.substring(0, visibleChars)
  const end = apiKey.substring(apiKey.length - visibleChars)
  const middle = '*'.repeat(Math.min(apiKey.length - visibleChars * 2, 12))

  return `${start}${middle}${end}`
}

/**
 * Format error message for display
 * @param {Error | string} error - Error object or message
 * @returns {string}
 */
export function formatErrorMessage(error) {
  if (typeof error === 'string') {
    return error
  }

  if (error && error.message) {
    return error.message
  }

  return 'An unknown error occurred'
}

/**
 * Format phone number
 * @param {string} phone - Phone number
 * @param {string} [format='###-####-####'] - Format pattern
 * @returns {string}
 */
export function formatPhoneNumber(phone, format = '###-####-####') {
  const cleaned = phone.replace(/\D/g, '')
  let formatted = format
  let digitIndex = 0

  for (let i = 0; i < formatted.length && digitIndex < cleaned.length; i++) {
    if (formatted[i] === '#') {
      formatted = formatted.substring(0, i) + cleaned[digitIndex] + formatted.substring(i + 1)
      digitIndex++
    }
  }

  return formatted.replace(/#/g, '')
}

/**
 * Format currency
 * @param {number} amount - Amount
 * @param {string} [currency='CNY'] - Currency code
 * @param {string} [locale='zh-CN'] - Locale
 * @returns {string}
 */
export function formatCurrency(amount, currency = 'CNY', locale = 'zh-CN') {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency
  }).format(amount)
}

/**
 * Format code for display (syntax highlighting placeholder)
 * @param {string} code - Code string
 * @param {string} [language='javascript'] - Programming language
 * @returns {string}
 */
export function formatCode(code, language = 'javascript') {
  // Placeholder for syntax highlighting
  // In production, integrate with a library like Prism.js or highlight.js
  return code.trim()
}

/**
 * Formatters object for easy access
 */
export const formatters = {
  date: formatDate,
  relativeTime: formatRelativeTime,
  fileSize: formatFileSize,
  number: formatNumber,
  percentage: formatPercentage,
  duration: formatDuration,
  truncate,
  capitalize,
  titleCase,
  stripMarkdown,
  messageContent: formatMessageContent,
  previewText: getPreviewText,
  apiKey: formatApiKey,
  errorMessage: formatErrorMessage,
  phoneNumber: formatPhoneNumber,
  currency: formatCurrency,
  code: formatCode
}

export default formatters
