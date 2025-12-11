<template>
  <!-- Modal Overlay -->
  <div class="modal-overlay" @click="handleOverlayClick">
    <div class="modal-container" @click.stop>
      <!-- Modal Header -->
      <div class="modal-header">
        <h2 class="modal-title">
          <i class="fa fa-magic"></i>
          Prompt Optimization Assistant
        </h2>
        <button class="close-btn" @click="closeModal" :disabled="loading">
          <i class="fa fa-times"></i>
        </button>
      </div>

      <!-- Modal Body -->
      <div class="modal-body">
        <!-- Function Buttons -->
        <div class="function-buttons">
          <button
            class="function-btn scene-btn"
            :class="{ active: selectedMode === 'scene' }"
            :disabled="loading || !userInput.trim()"
            @click="handleOptimize('scene')"
          >
            <i class="fa fa-paint-brush"></i>
            <span>Scene Optimization</span>
            <div class="btn-description">Scene Optimization: Enhance format specifications and content precision</div>
          </button>

          <button
            class="function-btn analysis-btn"
            :class="{ active: selectedMode === 'analysis' }"
            :disabled="loading || !userInput.trim()"
            @click="handleOptimize('analysis')"
          >
            <i class="fa fa-list-ol"></i>
            <span>Deep Analysis</span>
            <div class="btn-description">Deep Analysis: Break down into step-by-step executable instructions</div>
          </button>

          <button
            class="function-btn intelligent-btn"
            :class="{ active: selectedMode === 'intelligent' }"
            :disabled="loading || !userInput.trim()"
            @click="handleOptimize('intelligent')"
          >
            <i class="fa fa-lightbulb-o"></i>
            <span>Smart Optimization</span>
            <div class="btn-description">Smart Optimization: Deep understanding and enrichment of instruction requirements</div>
          </button>
        </div>

        <!-- Input Area -->
        <div class="input-section">
          <label class="section-label">
            <i class="fa fa-pencil"></i>
            Original Instruction Input
          </label>
          <textarea
            v-model="userInput"
            class="input-textarea"
            placeholder="Please enter your original instruction to optimize...&#10;Example: Help me write a login page code"
            rows="5"
            :disabled="loading"
          ></textarea>
        </div>

        <!-- Output Area -->
        <div class="output-section">
          <label class="section-label">
            <i class="fa fa-check-circle"></i>
            Optimized Prompt
          </label>

          <!-- Loading State -->
          <div v-if="loading" class="loading-state">
            <div class="loading-spinner">
              <i class="fa fa-spinner fa-spin"></i>
            </div>
            <p>{{ loadingText }}</p>
          </div>

          <!-- Output Textarea -->
          <textarea
            v-else
            v-model="optimizedPrompt"
            class="output-textarea"
            readonly
            placeholder="Optimized prompt will be displayed here..."
            rows="12"
          ></textarea>
        </div>

        <!-- Action Buttons -->
        <div class="action-buttons">
          <button
            class="action-btn copy-btn"
            :disabled="!optimizedPrompt || loading"
            @click="handleCopy"
          >
            <i class="fa fa-copy"></i>
            <span>Copy Optimized Result</span>
          </button>
          <button
            class="action-btn regenerate-btn"
            :disabled="loading"
            @click="handleRegenerate"
          >
            <i class="fa fa-refresh"></i>
            <span>Regenerate</span>
          </button>
        </div>

        <!-- Error Message -->
        <div v-if="errorMessage" class="error-message">
          <i class="fa fa-exclamation-triangle"></i>
          <span>{{ errorMessage }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import storage from '@/services/storage.service'
import { API_URLS } from '@/config/endpoints'

const emit = defineEmits(['close'])

// State
const userInput = ref('')
const optimizedPrompt = ref('')
const selectedMode = ref('')
const loading = ref(false)
const errorMessage = ref('')

// Loading text based on selected mode
const loadingText = computed(() => {
  switch (selectedMode.value) {
    case 'scene':
      return 'Performing scene optimization...'
    case 'analysis':
      return 'Performing deep analysis...'
    case 'intelligent':
      return 'Performing smart optimization...'
    default:
      return 'Processing...'
  }
})

// Handle optimization
const handleOptimize = async (mode) => {
  if (!userInput.value.trim()) {
    ElMessage.warning('Please enter your original instruction first')
    return
  }

  selectedMode.value = mode
  loading.value = true
  errorMessage.value = ''
  optimizedPrompt.value = '' // Clear previous result

  try {
    const token = storage.get('token')
    if (!token) {
      throw new Error('Please login first')
    }

    const response = await fetch(API_URLS.optimizeInstruction(), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        instruction: userInput.value,
        mode: mode
      })
    })

    if (!response.ok) {
      // Handle authentication errors
      if (response.status === 401) {
        ElMessage.error({
          message: 'Login session expired, please login again',
          duration: 4000,
          showClose: true
        })
        // Clear local storage
        storage.remove('token')
        storage.remove('user')
        // Redirect to login page
        setTimeout(() => {
          window.location.href = '/#/login'
        }, 2000)
        throw new Error('Authentication expired')
      }

      const errorData = await response.json()
      throw new Error(errorData.detail || 'API request failed')
    }

    const data = await response.json()

    if (data && data.optimized_instruction) {
      optimizedPrompt.value = data.optimized_instruction
      ElMessage.success('Prompt optimization completed!')
    } else {
      throw new Error('Invalid response format')
    }
  } catch (error) {
    console.error('Optimization failed:', error)

    // Don't show error for auth expiration
    if (error.message === 'Authentication expired') {
      return
    }

    errorMessage.value = error.message || 'Optimization failed, please try again'
    ElMessage.error(`Optimization failed: ${error.message}`)
  } finally {
    loading.value = false
  }
}

// Copy to clipboard
const handleCopy = async () => {
  try {
    await navigator.clipboard.writeText(optimizedPrompt.value)
    ElMessage.success({
      message: 'Copied to clipboard',
      duration: 3000
    })
  } catch (error) {
    console.error('Copy failed:', error)
    // Fallback for older browsers
    const textArea = document.createElement('textarea')
    textArea.value = optimizedPrompt.value
    textArea.style.position = 'fixed'
    textArea.style.left = '-999999px'
    document.body.appendChild(textArea)
    textArea.select()
    try {
      document.execCommand('copy')
      ElMessage.success('Copied to clipboard')
    } catch (err) {
      ElMessage.error('Copy failed, please copy manually')
    }
    document.body.removeChild(textArea)
  }
}

// Regenerate - clear all and start over
const handleRegenerate = () => {
  userInput.value = ''
  optimizedPrompt.value = ''
  selectedMode.value = ''
  errorMessage.value = ''
  ElMessage.info('Cleared, please enter again')
}

// Close modal
const closeModal = () => {
  emit('close')
}

// Handle overlay click
const handleOverlayClick = () => {
  if (!loading.value) {
    closeModal()
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
  animation: fadeIn 0.2s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.modal-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  max-width: 900px;
  width: 100%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    transform: translateY(-20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.dark .modal-container {
  background: #1F2937;
  color: #F9FAFB;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #E5E7EB;
}

.dark .modal-header {
  border-bottom-color: #4B5563;
}

.modal-title {
  font-size: 20px;
  font-weight: 600;
  color: #1F2937;
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
}

.dark .modal-title {
  color: #F9FAFB;
}

.modal-title i {
  color: #3B82F6;
}

.close-btn {
  background: none;
  border: none;
  color: #6B7280;
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  transition: all 0.2s;
}

.close-btn:hover:not(:disabled) {
  background: #F3F4F6;
  color: #374151;
}

.dark .close-btn:hover:not(:disabled) {
  background: #374151;
  color: #F9FAFB;
}

.close-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

/* Function Buttons */
.function-buttons {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 24px;
}

@media (max-width: 768px) {
  .function-buttons {
    grid-template-columns: 1fr;
  }
}

.function-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 16px 12px;
  border: 2px solid #E5E7EB;
  border-radius: 10px;
  background: #ffffff;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
}

.dark .function-btn {
  background: #374151;
  border-color: #4B5563;
  color: #F9FAFB;
}

.function-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.function-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.function-btn.active {
  border-color: #3B82F6;
  background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
}

.dark .function-btn.active {
  border-color: #60A5FA;
  background: linear-gradient(135deg, #1E3A8A 0%, #1E40AF 100%);
}

.function-btn i {
  font-size: 24px;
}

.scene-btn i {
  color: #8B5CF6;
}

.analysis-btn i {
  color: #10B981;
}

.intelligent-btn i {
  color: #F59E0B;
}

.function-btn span {
  font-size: 14px;
  font-weight: 500;
}

.btn-description {
  font-size: 11px;
  color: #6B7280;
  text-align: center;
  margin-top: 4px;
}

.dark .btn-description {
  color: #9CA3AF;
}

/* Input/Output Sections */
.input-section,
.output-section {
  margin-bottom: 20px;
}

.section-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 8px;
}

.dark .section-label {
  color: #F9FAFB;
}

.section-label i {
  color: #3B82F6;
}

.input-textarea,
.output-textarea {
  width: 100%;
  padding: 12px;
  font-size: 14px;
  line-height: 1.6;
  border: 2px solid #E5E7EB;
  border-radius: 8px;
  resize: vertical;
  outline: none;
  transition: all 0.3s;
  font-family: inherit;
}

.input-textarea {
  background: #ffffff;
  color: #1F2937;
}

.dark .input-textarea {
  background: #374151;
  border-color: #4B5563;
  color: #F9FAFB;
}

.input-textarea:focus {
  border-color: #3B82F6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.output-textarea {
  background: #F9FAFB;
  color: #374151;
}

.dark .output-textarea {
  background: #374151;
  border-color: #4B5563;
  color: #E5E7EB;
}

.input-textarea::placeholder,
.output-textarea::placeholder {
  color: #9CA3AF;
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  background: #F9FAFB;
  border-radius: 8px;
  border: 2px solid #E5E7EB;
}

.dark .loading-state {
  background: #374151;
  border-color: #4B5563;
}

.loading-spinner {
  font-size: 32px;
  color: #3B82F6;
  margin-bottom: 16px;
}

.dark .loading-spinner {
  color: #60A5FA;
}

.loading-state p {
  margin: 0;
  color: #6B7280;
  font-size: 14px;
}

.dark .loading-state p {
  color: #D1D5DB;
}

/* Action Buttons */
.action-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 20px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.copy-btn {
  background: #3B82F6;
  color: #ffffff;
}

.copy-btn:hover:not(:disabled) {
  background: #2563EB;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.regenerate-btn {
  background: #6B7280;
  color: #ffffff;
}

.dark .regenerate-btn {
  background: #4B5563;
}

.regenerate-btn:hover:not(:disabled) {
  background: #4B5563;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(107, 114, 128, 0.3);
}

.dark .regenerate-btn:hover:not(:disabled) {
  background: #374151;
}

/* Error Message */
.error-message {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #FEF2F2;
  border: 1px solid #FCA5A5;
  border-radius: 8px;
  color: #DC2626;
  font-size: 14px;
  margin-top: 16px;
}

.dark .error-message {
  background: #7F1D1D;
  border-color: #991B1B;
  color: #FCA5A5;
}

.error-message i {
  font-size: 16px;
}
</style>
