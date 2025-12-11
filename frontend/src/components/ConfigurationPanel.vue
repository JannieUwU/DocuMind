<template>
  <div class="configuration-panel" :class="{ 'dark-mode': isDark }">
    <div class="configuration-content">
      <!-- Current Model Configuration -->
      <div v-if="testPassed" class="model-info">
        <div class="model-info-title">
          <i class="fa fa-info-circle"></i>
          Current Model Configuration
        </div>
        <div class="model-list">
          <div class="model-item"><strong>LLM:</strong> gpt-4-turbo</div>
          <div class="model-item"><strong>Embedder:</strong> text-embedding-3-large</div>
          <div class="model-item"><strong>Reranker:</strong> BAAI/bge-reranker-v2-m3</div>
          <div class="model-item"><strong>System:</strong> Custom RAG Implementation</div>
        </div>
      </div>

      <!-- API Keys Configuration -->
      <div class="config-section-title">
        <i class="fa fa-key"></i>
        API Keys Configuration
      </div>

      <!-- OpenAI API Key -->
      <div class="config-item">
        <label class="config-label">
          <i class="fa fa-key"></i>
          OpenAI API Key
        </label>
        <input
          type="password"
          v-model="apiKey"
          placeholder="Enter OpenAI API Key"
          class="config-input"
        />
        <p class="config-help">For LLM (gpt-4-turbo) and Embedder (text-embedding-3-large)</p>
      </div>

      <!-- Reranker API Key -->
      <div class="config-item">
        <label class="config-label">
          <i class="fa fa-key"></i>
          Reranker API Key
        </label>
        <input
          type="password"
          v-model="rerankerKey"
          placeholder="Enter Reranker API Key"
          class="config-input"
        />
        <p class="config-help">For BAAI/bge-reranker-v2-m3 model</p>
      </div>

      <!-- Base URLs Configuration -->
      <div class="config-section-title">
        <i class="fa fa-link"></i>
        Base URLs (Optional)
      </div>

      <!-- OpenAI Base URL -->
      <div class="config-item">
        <label class="config-label">
          <i class="fa fa-link"></i>
          OpenAI Base URL
        </label>
        <input
          type="text"
          v-model="baseUrl"
          placeholder="Enter custom base URL"
          class="config-input"
        />
        <p class="config-help">Custom OpenAI API endpoint, leave empty for default</p>
      </div>

      <!-- Reranker Base URL -->
      <div class="config-item">
        <label class="config-label">
          <i class="fa fa-link"></i>
          Reranker Base URL
        </label>
        <input
          type="text"
          v-model="rerankerBaseUrl"
          placeholder="Enter custom base URL"
          class="config-input"
        />
        <p class="config-help">Custom Reranker API endpoint, leave empty for default</p>
      </div>

      <!-- Database Configuration -->
      <div class="config-section-title">
        <i class="fa fa-database"></i>
        Database Configuration
      </div>

      <!-- Database URL -->
      <div class="config-item">
        <label class="config-label">
          <i class="fa fa-database"></i>
          Database URL
        </label>
        <input
          type="text"
          v-model="databaseUrl"
          placeholder="sqlite:///raglite.sqlite"
          class="config-input"
        />
        <p class="config-help">Vector database or application database connection URL</p>
      </div>

      <!-- Configuration Status -->
      <div class="config-status">
        <div class="status-item">
          <span class="status-label">OpenAI API</span>
          <span :class="['status-tag', apiKey ? 'status-success' : 'status-info']">
            {{ apiKey ? 'Configured' : 'Not Configured' }}
          </span>
        </div>
        <div class="status-item">
          <span class="status-label">Reranker API</span>
          <span :class="['status-tag', rerankerKey ? 'status-success' : 'status-info']">
            {{ rerankerKey ? 'Configured' : 'Not Configured' }}
          </span>
        </div>
        <div class="status-item">
          <span class="status-label">OpenAI Base URL</span>
          <span :class="['status-tag', baseUrl ? 'status-success' : 'status-info']">
            {{ baseUrl ? 'Custom' : 'Default' }}
          </span>
        </div>
        <div class="status-item">
          <span class="status-label">Reranker Base URL</span>
          <span :class="['status-tag', rerankerBaseUrl ? 'status-success' : 'status-info']">
            {{ rerankerBaseUrl ? 'Custom' : 'Default' }}
          </span>
        </div>
      </div>

      <!-- Test Status Alert -->
      <div v-if="testPassed" class="test-status-success">
        <i class="fa fa-check-circle"></i>
        Configuration test passed! You can now save the configuration.
      </div>

      <!-- Action Buttons -->
      <div class="action-buttons">
        <button
          type="button"
          @click="testConnections"
          :disabled="testing"
          class="btn btn-secondary"
        >
          <i class="fa fa-plug"></i>
          {{ testing ? 'Testing...' : 'Test Connection' }}
        </button>
        <button
          type="button"
          @click="saveConfiguration"
          :disabled="saving || !testPassed"
          class="btn btn-primary"
          :title="!testPassed ? 'Please test connection first' : ''"
        >
          <i class="fa fa-check"></i>
          {{ saving ? 'Saving...' : 'Save Configuration' }}
        </button>
        <button
          type="button"
          @click="resetConfiguration"
          class="btn btn-outline"
        >
          <i class="fa fa-refresh"></i>
          Reset
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/utils/api'
import { themeManager } from '@/utils/theme'
import storage from '@/services/storage.service'

const emit = defineEmits(['close'])

// 主题Status
const isDark = computed(() => themeManager.getCurrentTheme() === 'dark')

// 使用独立的 ref 确保输入正常工作
const apiKey = ref('')
const rerankerKey = ref('')
const baseUrl = ref('')
const rerankerBaseUrl = ref('')
const databaseUrl = ref('')

const saving = ref(false)
const testing = ref(false)
const testPassed = ref(false) // 新增：测试是否通过的Status

// 加载Configuration
const loadConfiguration = () => {
  const savedConfig = storage.get('api-configuration')
  if (savedConfig) {
    try {
      // Support both new and legacy config formats
      apiKey.value = savedConfig.apiKey || savedConfig.openaiApiKey || ''
      rerankerKey.value = savedConfig.rerankerKey || ''
      baseUrl.value = savedConfig.baseUrl || ''
      rerankerBaseUrl.value = savedConfig.rerankerBaseUrl || ''
      databaseUrl.value = savedConfig.databaseUrl || ''
    } catch (e) {
      console.error('加载Configuration failed:', e)
    }
  }
}

// Show success modal
const showSuccessModal = (message) => {
  const currentTheme = themeManager.getCurrentTheme()
  const modal = document.createElement('div')
  modal.className = currentTheme === 'dark' ? 'api-success-modal dark-mode' : 'api-success-modal'
  modal.innerHTML = `
    <div class="modal-overlay">
      <div class="modal-content">
        <div class="modal-icon success">
          <i class="fa fa-check-circle"></i>
        </div>
        <h3 class="modal-title">Configuration Successful</h3>
        <p class="modal-message">${message}</p>
        <button class="modal-btn">OK</button>
      </div>
    </div>
  `

  document.body.appendChild(modal)

  // 点击按钮或背景Close弹窗
  modal.querySelector('.modal-btn').addEventListener('click', () => modal.remove())
  modal.querySelector('.modal-overlay').addEventListener('click', (e) => {
    if (e.target.className === 'modal-overlay') modal.remove()
  })

  // 添加Success弹窗样式
  if (!document.getElementById('api-success-modal-styles')) {
    const style = document.createElement('style')
    style.id = 'api-success-modal-styles'
    style.textContent = `
      .api-success-modal {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        z-index: 9999;
        animation: fadeIn 0.2s ease-in-out;
      }
      .api-success-modal .modal-overlay {
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px;
      }
      .api-success-modal .modal-content {
        background: white;
        border-radius: 12px;
        padding: 32px;
        max-width: 400px;
        width: 100%;
        text-align: center;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        animation: slideIn 0.3s ease-out;
      }
      .api-success-modal.dark-mode .modal-content {
        background: #1F2937;
        color: #F9FAFB;
      }
      .api-success-modal .modal-icon.success {
        width: 64px;
        height: 64px;
        border-radius: 50%;
        background-color: #D1FAE5;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 20px;
      }
      .api-success-modal .modal-icon.success i {
        font-size: 32px;
        color: #059669;
      }
      .api-success-modal .modal-title {
        font-size: 20px;
        font-weight: 600;
        color: #1F2937;
        margin-bottom: 12px;
      }
      .api-success-modal.dark-mode .modal-title {
        color: #F9FAFB;
      }
      .api-success-modal .modal-message {
        font-size: 14px;
        color: #6B7280;
        line-height: 1.6;
        margin-bottom: 20px;
      }
      .api-success-modal.dark-mode .modal-message {
        color: #D1D5DB;
      }
      .api-success-modal .modal-btn {
        background-color: #3b82f6;
        color: white;
        border: none;
        padding: 10px 24px;
        border-radius: 6px;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        transition: background-color 0.2s;
      }
      .api-success-modal .modal-btn:hover {
        background-color: #2563eb;
      }
    `
    document.head.appendChild(style)
  }
}

// Save configuration
const saveConfiguration = async () => {
  // Must pass test first
  if (!testPassed.value) {
    ElMessage.warning('Please test the connection first and ensure it passes before saving')
    return
  }

  saving.value = true

  try {
    if (!apiKey.value) {
      ElMessage.warning('Please configure OpenAI API Key')
      saving.value = false
      return
    }

    if (!rerankerKey.value) {
      ElMessage.warning('Please configure Reranker API Key')
      saving.value = false
      return
    }

    const configData = {
      apiKey: apiKey.value || null,
      rerankerKey: rerankerKey.value || null,
      baseUrl: baseUrl.value || null,
      rerankerBaseUrl: rerankerBaseUrl.value || null,
      databaseUrl: databaseUrl.value || 'sqlite:///raglite.sqlite'
    }

    // Save to localStorage
    storage.set('api-configuration', configData)

    // Dispatch custom event to notify other components
    window.dispatchEvent(new CustomEvent('config-updated', { detail: configData }))

    // Try to save to backend
    try {
      const response = await api.post('/config', configData)
      if (response.data.success) {
        showSuccessModal('Configuration saved successfully. Backend connection established. You can now start using the Custom RAG chat feature!')
      }
    } catch (error) {
      console.error('Backend save failed:', error)
      if (error.response?.status === 401) {
        showSuccessModal('Configuration saved locally. Please login first to sync configuration to backend.')
      } else {
        showSuccessModal('Configuration saved to local storage.')
      }
    }
  } catch (error) {
    console.error('Failed to save configuration:', error)
    ElMessage.error('Failed to save configuration')
  } finally {
    saving.value = false
  }
}

// Test connections
const testConnections = async () => {
  testing.value = true
  testPassed.value = false // Reset test status

  try {
    // Validate API keys
    if (!apiKey.value) {
      ElMessage.warning('Please enter OpenAI API Key')
      testing.value = false
      return
    }

    if (!rerankerKey.value) {
      ElMessage.warning('Please enter Reranker API Key')
      testing.value = false
      return
    }

    const configData = {
      apiKey: apiKey.value || null,
      rerankerKey: rerankerKey.value || null,
      baseUrl: baseUrl.value || null,
      rerankerBaseUrl: rerankerBaseUrl.value || null,
      databaseUrl: databaseUrl.value || 'sqlite:///raglite.sqlite'
    }

    // Save config to backend first
    try {
      await api.post('/config', configData)
    } catch (error) {
      if (error.response?.status === 401 || error.response?.status === 403) {
        ElMessage.error('Session expired, please login again')
        // Clear local token
        storage.remove('token')
        storage.remove('user')
        // Redirect to login page
        setTimeout(() => {
          window.location.href = '/#/login'
        }, 1500)
        testing.value = false
        testPassed.value = false
        return
      }
      throw error
    }

    // Test connections
    const response = await api.post('/config/test')

    if (response.data) {
      // Check for any failed connections
      const results = response.data
      let hasError = false
      let errorMessages = []

      if (results.openai && results.openai.status === 'error') {
        hasError = true
        errorMessages.push('OpenAI: ' + results.openai.message)
      }
      if (results.database && results.database.status === 'error') {
        hasError = true
        errorMessages.push('Database: ' + results.database.message)
      }

      if (hasError) {
        // Test failed
        testPassed.value = false
        const errorText = errorMessages.join('<br>')
        showApiErrorModal('API connection test failed:<br>' + errorText)
        ElMessage.error('Configuration test failed, please check configuration and retry')
      } else {
        // Test succeeded
        testPassed.value = true
        showSuccessModal('All API connections tested successfully! You can now save the configuration.')
      }
    }
  } catch (error) {
    console.error('Connection test failed:', error)
    testPassed.value = false
    const errorDetail = error.response?.data?.detail || error.message || 'Unknown error'
    showApiErrorModal(`API connection test failed: ${errorDetail}`)
    ElMessage.error('Configuration test failed')
  } finally {
    testing.value = false
  }
}

// Show API error modal
const showApiErrorModal = (errorMsg = 'Unable to connect to API service. Please check if your API Key and Base URL are correct.') => {
  // Create a global error modal
  const modal = document.createElement('div')
  // Check current theme, add dark-mode class if dark
  const currentTheme = themeManager.getCurrentTheme()
  modal.className = currentTheme === 'dark' ? 'api-error-modal dark-mode' : 'api-error-modal'
  modal.innerHTML = `
    <div class="modal-overlay">
      <div class="modal-content">
        <div class="modal-icon">
          <i class="fa fa-exclamation-triangle"></i>
        </div>
        <h3 class="modal-title">API Connection Failed</h3>
        <p class="modal-message">${errorMsg}</p>
      </div>
    </div>
  `

  document.body.appendChild(modal)

  // Click background to close modal
  modal.querySelector('.modal-overlay').addEventListener('click', (e) => {
    if (e.target.className === 'modal-overlay') {
      modal.remove()
    }
  })

  // Add styles
  if (!document.getElementById('api-error-modal-styles')) {
    const style = document.createElement('style')
    style.id = 'api-error-modal-styles'
    style.textContent = `
      .api-error-modal {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        z-index: 9999;
        animation: fadeIn 0.2s ease-in-out;
      }

      .modal-overlay {
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px;
      }

      .modal-content {
        background: white;
        border-radius: 12px;
        padding: 32px;
        max-width: 400px;
        width: 100%;
        text-align: center;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        animation: slideIn 0.3s ease-out;
      }

      .dark-mode .modal-content {
        background: #1F2937;
        color: #F9FAFB;
      }

      .modal-icon {
        width: 64px;
        height: 64px;
        border-radius: 50%;
        background-color: #FEF3C7;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 20px;
      }

      .modal-icon i {
        font-size: 32px;
        color: #F59E0B;
      }

      .modal-title {
        font-size: 20px;
        font-weight: 600;
        color: #1F2937;
        margin-bottom: 12px;
      }

      .dark-mode .modal-title {
        color: #F9FAFB;
      }

      .modal-message {
        font-size: 14px;
        color: #6B7280;
        line-height: 1.6;
      }

      .dark-mode .modal-message {
        color: #D1D5DB;
      }

      @keyframes fadeIn {
        from {
          opacity: 0;
        }
        to {
          opacity: 1;
        }
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
    `
    document.head.appendChild(style)
  }
}

// Reset configuration
const resetConfiguration = () => {
  apiKey.value = ''
  rerankerKey.value = ''
  baseUrl.value = ''
  rerankerBaseUrl.value = ''
  databaseUrl.value = ''
  testPassed.value = false // Reset test status
  storage.remove('api-configuration')
  ElMessage.info('Configuration has been reset')
}

// Watch for config changes, reset test status
watch([apiKey, rerankerKey, baseUrl, rerankerBaseUrl, databaseUrl], () => {
  testPassed.value = false
})

onMounted(() => {
  loadConfiguration()
})
</script>

<style scoped>
.configuration-panel {
  width: 100%;
}

.configuration-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.model-info {
  padding: 16px;
  background: #e0f2fe;
  border: 1px solid #0ea5e9;
  border-radius: 8px;
  margin-bottom: 8px;
}

.model-info-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #0369a1;
  margin-bottom: 12px;
}

.model-info-title i {
  color: #0284c7;
}

.model-list {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.model-item {
  font-size: 13px;
  color: #0c4a6e;
  padding: 4px 0;
}

.model-item strong {
  color: #075985;
}

.dark-mode .model-info {
  background: #164e63;
  border-color: #0891b2;
}

.dark-mode .model-info-title {
  color: #67e8f9;
}

.dark-mode .model-info-title i {
  color: #22d3ee;
}

.dark-mode .model-item {
  color: #cffafe;
}

.dark-mode .model-item strong {
  color: #a5f3fc;
}

.config-section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  padding: 8px 0;
  border-bottom: 1px solid #e5e7eb;
  margin-top: 8px;
}

.config-section-title:first-child {
  margin-top: 0;
}

.config-section-title i {
  color: #3b82f6;
  font-size: 14px;
}

.config-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.config-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.config-label i {
  color: #6b7280;
  font-size: 14px;
}

.config-input {
  width: 100%;
  padding: 10px 12px;
  font-size: 14px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
  background-color: #fff;
  color: #374151;
}

.config-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.config-input::placeholder {
  color: #9ca3af;
}

.config-help {
  font-size: 12px;
  color: #6b7280;
  margin: 0;
}

.test-status-success {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #d1fae5;
  border: 1px solid #10b981;
  border-radius: 8px;
  color: #065f46;
  font-size: 14px;
  font-weight: 500;
  animation: slideIn 0.3s ease-out;
}

.test-status-success i {
  color: #059669;
  font-size: 16px;
}

.config-status {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

@media (max-width: 768px) {
  .model-list {
    grid-template-columns: 1fr;
  }

  .config-status {
    grid-template-columns: 1fr;
  }
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-label {
  font-size: 12px;
  color: #374151;
  font-weight: 500;
}

.status-tag {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status-info {
  background-color: #e5e7eb;
  color: #6b7280;
}

.status-success {
  background-color: #d1fae5;
  color: #059669;
}

.action-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  font-size: 14px;
  font-weight: 500;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background-color: #3b82f6;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #2563eb;
}

.btn-secondary {
  background-color: #6b7280;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background-color: #4b5563;
}

.btn-outline {
  background-color: transparent;
  color: #6b7280;
  border: 1px solid #d1d5db;
}

.btn-outline:hover:not(:disabled) {
  background-color: #f3f4f6;
}

/* Dark mode styles */
.dark-mode .config-section-title {
  color: #f9fafb;
  border-bottom-color: #4b5563;
}

.dark-mode .config-section-title i {
  color: #60a5fa;
}

.dark-mode .config-label {
  color: #f9fafb;
}

.dark-mode .config-label i {
  color: #9ca3af;
}

.dark-mode .config-input {
  background-color: #374151;
  border-color: #4b5563;
  color: #f9fafb;
}

.dark-mode .config-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

.dark-mode .config-input::placeholder {
  color: #9ca3af;
}

.dark-mode .config-help {
  color: #9ca3af;
}

.dark-mode .config-status {
  background-color: #374151;
  border-color: #4b5563;
}

.dark-mode .status-label {
  color: #f9fafb;
}

.dark-mode .status-info {
  background-color: #4b5563;
  color: #d1d5db;
}

.dark-mode .status-success {
  background-color: #065f46;
  color: #6ee7b7;
}

.dark-mode .btn-outline {
  border-color: #4b5563;
  color: #d1d5db;
}

.dark-mode .btn-outline:hover:not(:disabled) {
  background-color: #374151;
}

.dark-mode .test-status-success {
  background: #065f46;
  border-color: #10b981;
  color: #6ee7b7;
}

.dark-mode .test-status-success i {
  color: #6ee7b7;
}

@media (max-width: 640px) {
  .config-status {
    grid-template-columns: 1fr;
  }

  .action-buttons {
    flex-direction: column;
  }

  .btn {
    width: 100%;
    justify-content: center;
  }
}
</style>
