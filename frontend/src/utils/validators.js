/**
 * Form Validation Utilities
 *
 * Centralized validation logic to avoid duplication.
 * @typedef {import('@/types/api.types').ValidationResult} ValidationResult
 */

import { VALIDATION } from '@/config/constants'

/**
 * Validation result type
 * @typedef {Object} ValidatorResult
 * @property {boolean} valid - Whether validation passed
 * @property {string} [message] - Error message if validation failed
 */

/**
 * Email validator
 * @param {string} email - Email to validate
 * @returns {ValidatorResult}
 */
export function validateEmail(email) {
  if (!email || !email.trim()) {
    return { valid: false, message: 'Email is required' }
  }

  if (!VALIDATION.EMAIL_REGEX.test(email.trim())) {
    return { valid: false, message: 'Please enter a valid email' }
  }

  return { valid: true }
}

/**
 * Username validator
 * @param {string} username - Username to validate
 * @returns {ValidatorResult}
 */
export function validateUsername(username) {
  if (!username || !username.trim()) {
    return { valid: false, message: 'Username is required' }
  }

  const trimmed = username.trim()

  if (trimmed.length < VALIDATION.USERNAME_MIN_LENGTH) {
    return {
      valid: false,
      message: `Username must be at least ${VALIDATION.USERNAME_MIN_LENGTH} characters`
    }
  }

  if (trimmed.length > VALIDATION.USERNAME_MAX_LENGTH) {
    return {
      valid: false,
      message: `Username must be less than ${VALIDATION.USERNAME_MAX_LENGTH} characters`
    }
  }

  // Check for valid characters (alphanumeric, underscore, dash)
  if (!/^[a-zA-Z0-9_-]+$/.test(trimmed)) {
    return {
      valid: false,
      message: 'Username can only contain letters, numbers, underscore and dash'
    }
  }

  return { valid: true }
}

/**
 * Password validator
 * @param {string} password - Password to validate
 * @param {Object} [options] - Validation options
 * @param {boolean} [options.requireUppercase=true] - Require uppercase letter
 * @param {boolean} [options.requireLowercase=true] - Require lowercase letter
 * @param {boolean} [options.requireNumber=true] - Require number
 * @param {boolean} [options.requireSpecial=false] - Require special character
 * @returns {ValidatorResult}
 */
export function validatePassword(password, options = {}) {
  const {
    requireUppercase = true,
    requireLowercase = true,
    requireNumber = true,
    requireSpecial = false
  } = options

  if (!password || !password.trim()) {
    return { valid: false, message: 'Password is required' }
  }

  if (password.length < VALIDATION.PASSWORD_MIN_LENGTH) {
    return {
      valid: false,
      message: `Password must be at least ${VALIDATION.PASSWORD_MIN_LENGTH} characters`
    }
  }

  if (password.length > VALIDATION.PASSWORD_MAX_LENGTH) {
    return {
      valid: false,
      message: `Password must be less than ${VALIDATION.PASSWORD_MAX_LENGTH} characters`
    }
  }

  if (requireUppercase && !/[A-Z]/.test(password)) {
    return {
      valid: false,
      message: 'Password must contain at least one uppercase letter'
    }
  }

  if (requireLowercase && !/[a-z]/.test(password)) {
    return {
      valid: false,
      message: 'Password must contain at least one lowercase letter'
    }
  }

  if (requireNumber && !/[0-9]/.test(password)) {
    return {
      valid: false,
      message: 'Password must contain at least one number'
    }
  }

  if (requireSpecial && !/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    return {
      valid: false,
      message: 'Password must contain at least one special character'
    }
  }

  return { valid: true }
}

/**
 * Verification code validator
 * @param {string} code - Verification code to validate
 * @returns {ValidatorResult}
 */
export function validateVerificationCode(code) {
  if (!code || !code.trim()) {
    return { valid: false, message: 'Verification code is required' }
  }

  const trimmed = code.trim()

  if (trimmed.length !== VALIDATION.VERIFICATION_CODE_LENGTH) {
    return {
      valid: false,
      message: `Verification code must be ${VALIDATION.VERIFICATION_CODE_LENGTH} digits`
    }
  }

  if (!/^\d+$/.test(trimmed)) {
    return {
      valid: false,
      message: 'Verification code must contain only numbers'
    }
  }

  return { valid: true }
}

/**
 * Password confirmation validator
 * @param {string} password - Original password
 * @param {string} confirmPassword - Confirmation password
 * @returns {ValidatorResult}
 */
export function validatePasswordConfirmation(password, confirmPassword) {
  if (!confirmPassword || !confirmPassword.trim()) {
    return { valid: false, message: 'Please confirm your password' }
  }

  if (password !== confirmPassword) {
    return { valid: false, message: 'Passwords do not match' }
  }

  return { valid: true }
}

/**
 * Required field validator
 * @param {any} value - Value to validate
 * @param {string} fieldName - Name of the field
 * @returns {ValidatorResult}
 */
export function validateRequired(value, fieldName = 'This field') {
  if (value === null || value === undefined || value === '') {
    return { valid: false, message: `${fieldName} is required` }
  }

  if (typeof value === 'string' && !value.trim()) {
    return { valid: false, message: `${fieldName} is required` }
  }

  return { valid: true }
}

/**
 * Min length validator
 * @param {string} value - Value to validate
 * @param {number} minLength - Minimum length
 * @param {string} fieldName - Name of the field
 * @returns {ValidatorResult}
 */
export function validateMinLength(value, minLength, fieldName = 'This field') {
  if (!value || value.length < minLength) {
    return {
      valid: false,
      message: `${fieldName} must be at least ${minLength} characters`
    }
  }

  return { valid: true }
}

/**
 * Max length validator
 * @param {string} value - Value to validate
 * @param {number} maxLength - Maximum length
 * @param {string} fieldName - Name of the field
 * @returns {ValidatorResult}
 */
export function validateMaxLength(value, maxLength, fieldName = 'This field') {
  if (value && value.length > maxLength) {
    return {
      valid: false,
      message: `${fieldName} must be less than ${maxLength} characters`
    }
  }

  return { valid: true }
}

/**
 * URL validator
 * @param {string} url - URL to validate
 * @returns {ValidatorResult}
 */
export function validateUrl(url) {
  if (!url || !url.trim()) {
    return { valid: false, message: 'URL is required' }
  }

  try {
    new URL(url)
    return { valid: true }
  } catch {
    return { valid: false, message: 'Please enter a valid URL' }
  }
}

/**
 * Composite validators for common forms
 */

/**
 * Validate login form
 * @param {Object} data - Login form data
 * @param {string} data.username - Username
 * @param {string} data.password - Password
 * @returns {ValidationResult}
 */
export function validateLoginForm(data) {
  const errors = {}

  const usernameResult = validateUsername(data.username)
  if (!usernameResult.valid) {
    errors.username = usernameResult.message
  }

  const passwordResult = validateRequired(data.password, 'Password')
  if (!passwordResult.valid) {
    errors.password = passwordResult.message
  }

  return {
    valid: Object.keys(errors).length === 0,
    errors
  }
}

/**
 * Validate registration form
 * @param {Object} data - Registration form data
 * @param {string} data.username - Username
 * @param {string} data.email - Email
 * @param {string} data.password - Password
 * @param {string} data.confirmPassword - Password confirmation
 * @param {string} data.verificationCode - Verification code
 * @returns {ValidationResult}
 */
export function validateRegisterForm(data) {
  const errors = {}

  const usernameResult = validateUsername(data.username)
  if (!usernameResult.valid) {
    errors.username = usernameResult.message
  }

  const emailResult = validateEmail(data.email)
  if (!emailResult.valid) {
    errors.email = emailResult.message
  }

  const passwordResult = validatePassword(data.password)
  if (!passwordResult.valid) {
    errors.password = passwordResult.message
  }

  const confirmResult = validatePasswordConfirmation(data.password, data.confirmPassword)
  if (!confirmResult.valid) {
    errors.confirmPassword = confirmResult.message
  }

  const codeResult = validateVerificationCode(data.verificationCode)
  if (!codeResult.valid) {
    errors.verificationCode = codeResult.message
  }

  return {
    valid: Object.keys(errors).length === 0,
    errors
  }
}

/**
 * Validate reset password form
 * @param {Object} data - Reset password form data
 * @param {string} data.email - Email
 * @param {string} data.verificationCode - Verification code
 * @param {string} data.newPassword - New password
 * @param {string} data.confirmPassword - Password confirmation
 * @returns {ValidationResult}
 */
export function validateResetPasswordForm(data) {
  const errors = {}

  const emailResult = validateEmail(data.email)
  if (!emailResult.valid) {
    errors.email = emailResult.message
  }

  const codeResult = validateVerificationCode(data.verificationCode)
  if (!codeResult.valid) {
    errors.verificationCode = codeResult.message
  }

  const passwordResult = validatePassword(data.newPassword)
  if (!passwordResult.valid) {
    errors.newPassword = passwordResult.message
  }

  const confirmResult = validatePasswordConfirmation(data.newPassword, data.confirmPassword)
  if (!confirmResult.valid) {
    errors.confirmPassword = confirmResult.message
  }

  return {
    valid: Object.keys(errors).length === 0,
    errors
  }
}

/**
 * Create a validator from multiple validators
 * @param {...Function} validators - Validator functions
 * @returns {Function}
 */
export function composeValidators(...validators) {
  return (value) => {
    for (const validator of validators) {
      const result = validator(value)
      if (!result.valid) {
        return result
      }
    }
    return { valid: true }
  }
}

/**
 * Validators object for easy access
 */
export const validators = {
  email: validateEmail,
  username: validateUsername,
  password: validatePassword,
  verificationCode: validateVerificationCode,
  passwordConfirmation: validatePasswordConfirmation,
  required: validateRequired,
  minLength: validateMinLength,
  maxLength: validateMaxLength,
  url: validateUrl
}

/**
 * Form validators
 */
export const formValidators = {
  login: validateLoginForm,
  register: validateRegisterForm,
  resetPassword: validateResetPasswordForm
}

export default {
  validators,
  formValidators,
  composeValidators
}
