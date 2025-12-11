/**
 * HTML Sanitization Utilities
 *
 * Provides secure HTML sanitization using DOMPurify to prevent XSS attacks.
 * Use these utilities whenever rendering user-generated or AI-generated HTML.
 */

import DOMPurify from 'dompurify'

/**
 * Default sanitization configuration
 * Allows common markdown/HTML elements while blocking dangerous content
 */
const DEFAULT_CONFIG = {
  ALLOWED_TAGS: [
    // Text formatting
    'p', 'br', 'strong', 'em', 'b', 'i', 'u', 's',
    // Code
    'code', 'pre',
    // Quotes
    'blockquote',
    // Links
    'a',
    // Lists
    'ul', 'ol', 'li',
    // Headings
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    // Tables
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
    // Other
    'hr', 'div', 'span'
  ],
  ALLOWED_ATTR: [
    'href',    // For links
    'title',   // For tooltips
    'target',  // For link targets
    'rel',     // For link relationships
    'class'    // For styling
  ],
  // Prevent javascript:, data:, vbscript:, etc. URLs
  ALLOWED_URI_REGEXP: /^(?:(?:(?:f|ht)tps?|mailto|tel|callto|sms|cid|xmpp):|[^a-z]|[a-z+.\-]+(?:[^a-z+.\-:]|$))/i
}

/**
 * Strict sanitization configuration
 * Only allows basic text formatting, no links or complex elements
 */
const STRICT_CONFIG = {
  ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'code', 'pre'],
  ALLOWED_ATTR: []
}

/**
 * Permissive sanitization configuration
 * Allows more HTML elements for rich content (still blocks dangerous elements)
 */
const PERMISSIVE_CONFIG = {
  ...DEFAULT_CONFIG,
  ALLOWED_TAGS: [
    ...DEFAULT_CONFIG.ALLOWED_TAGS,
    'img', 'video', 'audio', 'source',
    'details', 'summary',
    'sup', 'sub', 'mark', 'del', 'ins'
  ],
  ALLOWED_ATTR: [
    ...DEFAULT_CONFIG.ALLOWED_ATTR,
    'src', 'alt', 'width', 'height',
    'controls', 'autoplay', 'loop', 'muted',
    'open'
  ]
}

/**
 * Sanitize HTML content using default configuration
 *
 * @param {string} html - HTML content to sanitize
 * @returns {string} Sanitized HTML safe for rendering
 *
 * @example
 * const userInput = '<script>alert("XSS")</script>Hello'
 * const safe = sanitizeHtml(userInput)
 * // Result: 'Hello' (script removed)
 */
export function sanitizeHtml(html) {
  if (!html) return ''
  return DOMPurify.sanitize(html, DEFAULT_CONFIG)
}

/**
 * Sanitize HTML content using strict configuration
 * Use for untrusted or high-risk content
 *
 * @param {string} html - HTML content to sanitize
 * @returns {string} Sanitized HTML with minimal allowed tags
 *
 * @example
 * const untrusted = '<a href="javascript:alert()">Click</a>'
 * const safe = sanitizeHtmlStrict(untrusted)
 * // Result: 'Click' (link removed)
 */
export function sanitizeHtmlStrict(html) {
  if (!html) return ''
  return DOMPurify.sanitize(html, STRICT_CONFIG)
}

/**
 * Sanitize HTML content using permissive configuration
 * Use for trusted content that needs rich formatting
 *
 * @param {string} html - HTML content to sanitize
 * @returns {string} Sanitized HTML with more allowed tags
 *
 * @example
 * const richContent = '<img src="photo.jpg" alt="Photo"><p>Description</p>'
 * const safe = sanitizeHtmlPermissive(richContent)
 * // Result: Same as input (allowed elements)
 */
export function sanitizeHtmlPermissive(html) {
  if (!html) return ''
  return DOMPurify.sanitize(html, PERMISSIVE_CONFIG)
}

/**
 * Sanitize HTML content using custom configuration
 *
 * @param {string} html - HTML content to sanitize
 * @param {object} config - DOMPurify configuration object
 * @returns {string} Sanitized HTML
 *
 * @example
 * const html = '<div id="test">Content</div>'
 * const safe = sanitizeHtmlCustom(html, {
 *   ALLOWED_TAGS: ['div'],
 *   ALLOWED_ATTR: ['id']
 * })
 * // Result: '<div id="test">Content</div>'
 */
export function sanitizeHtmlCustom(html, config) {
  if (!html) return ''
  return DOMPurify.sanitize(html, config)
}

/**
 * Sanitize markdown-rendered HTML
 * Optimized for markdown content from marked.parse()
 *
 * @param {string} markdownHtml - HTML from markdown parser
 * @returns {string} Sanitized HTML safe for rendering
 *
 * @example
 * import { marked } from 'marked'
 * const markdown = '# Hello\n**Bold** text'
 * const html = marked.parse(markdown)
 * const safe = sanitizeMarkdown(html)
 */
export function sanitizeMarkdown(markdownHtml) {
  return sanitizeHtml(markdownHtml)
}

/**
 * Check if HTML contains potentially dangerous content
 * Useful for logging/monitoring suspicious content
 *
 * @param {string} html - HTML content to check
 * @returns {boolean} True if dangerous content detected
 *
 * @example
 * const malicious = '<script>alert("XSS")</script>'
 * if (isDangerousHtml(malicious)) {
 *   console.warn('Blocked malicious content')
 * }
 */
export function isDangerousHtml(html) {
  if (!html) return false

  const sanitized = DOMPurify.sanitize(html, DEFAULT_CONFIG)

  // If sanitization changed the content, it contained dangerous elements
  return html !== sanitized
}

/**
 * Get list of removed elements during sanitization
 * Useful for debugging or security monitoring
 *
 * @param {string} html - HTML content to analyze
 * @returns {string[]} Array of removed element types
 *
 * @example
 * const html = '<script>alert(1)</script><img src=x onerror=alert(2)>'
 * const removed = getRemovedElements(html)
 * // Result: ['SCRIPT', 'onerror attribute']
 */
export function getRemovedElements(html) {
  if (!html) return []

  const removed = []

  // Configure DOMPurify hooks to track removed elements
  DOMPurify.addHook('uponSanitizeElement', (node, data) => {
    if (!data.allowedTags[data.tagName]) {
      removed.push(data.tagName)
    }
  })

  DOMPurify.addHook('uponSanitizeAttribute', (node, data) => {
    if (!data.allowedAttributes[data.attrName]) {
      removed.push(`${data.attrName} attribute`)
    }
  })

  // Perform sanitization to trigger hooks
  DOMPurify.sanitize(html, DEFAULT_CONFIG)

  // Clean up hooks
  DOMPurify.removeAllHooks()

  return [...new Set(removed)] // Remove duplicates
}

/**
 * Sanitize and validate URL
 * Ensures URL is safe for use in href attributes
 *
 * @param {string} url - URL to sanitize
 * @returns {string | null} Sanitized URL or null if invalid/dangerous
 *
 * @example
 * sanitizeUrl('https://example.com') // 'https://example.com'
 * sanitizeUrl('javascript:alert(1)') // null
 */
export function sanitizeUrl(url) {
  if (!url) return null

  // Block dangerous protocols
  const dangerousProtocols = /^(javascript|data|vbscript|file|about):/i
  if (dangerousProtocols.test(url.trim())) {
    return null
  }

  // Allow safe protocols
  const safeProtocols = /^(https?|mailto|tel|sms):/i
  if (!safeProtocols.test(url.trim()) && !url.startsWith('/') && !url.startsWith('#')) {
    return null
  }

  return url
}

/**
 * Strip all HTML tags from content
 * Returns plain text only
 *
 * @param {string} html - HTML content
 * @returns {string} Plain text without any HTML tags
 *
 * @example
 * const html = '<p>Hello <strong>world</strong>!</p>'
 * const text = stripHtml(html)
 * // Result: 'Hello world!'
 */
export function stripHtml(html) {
  if (!html) return ''

  // Use DOMPurify with no allowed tags to strip all HTML
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: [],
    ALLOWED_ATTR: []
  })
}

/**
 * Export configurations for direct use if needed
 */
export const CONFIGS = {
  DEFAULT: DEFAULT_CONFIG,
  STRICT: STRICT_CONFIG,
  PERMISSIVE: PERMISSIVE_CONFIG
}

/**
 * Export DOMPurify instance for advanced use cases
 */
export { DOMPurify }

export default {
  sanitizeHtml,
  sanitizeHtmlStrict,
  sanitizeHtmlPermissive,
  sanitizeHtmlCustom,
  sanitizeMarkdown,
  isDangerousHtml,
  getRemovedElements,
  sanitizeUrl,
  stripHtml,
  CONFIGS,
  DOMPurify
}
