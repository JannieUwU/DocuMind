<!--
  StorageQuotaIndicator Component

  Displays storage usage and provides cleanup options.
-->
<template>
  <div class="storage-quota-indicator">
    <!-- Compact indicator (always visible) -->
    <div
      v-if="!expanded"
      class="compact-indicator"
      :class="`status-${statusColor}`"
      @click="expanded = true"
      title="Click to see storage details"
    >
      <i class="fa fa-database text-xs"></i>
      <span class="text-xs ml-1">{{ storageInfo.percentage }}%</span>
    </div>

    <!-- Expanded view -->
    <div v-else class="expanded-view dark:bg-surface-elevated dark:text-text-primary">
      <!-- Header -->
      <div class="header">
        <h3 class="text-sm font-semibold dark:text-text-primary">Storage Usage</h3>
        <button @click="expanded = false" class="close-btn">
          <i class="fa fa-times text-xs"></i>
        </button>
      </div>

      <!-- Progress bar -->
      <div class="progress-container">
        <div class="progress-bar">
          <div
            class="progress-fill"
            :class="`bg-${statusColor}`"
            :style="{ width: `${Math.min(storageInfo.percentage, 100)}%` }"
          ></div>
        </div>
        <div class="progress-text text-xs dark:text-text-secondary">
          {{ storageInfo.formattedUsed }} / {{ storageInfo.formattedMax }}
          ({{ storageInfo.percentage }}%)
        </div>
      </div>

      <!-- Status message -->
      <div
        class="status-message text-xs"
        :class="`text-${statusColor}`"
      >
        <i class="fa fa-info-circle mr-1"></i>
        {{ statusMessage }}
      </div>

      <!-- Info -->
      <div class="info-grid text-xs dark:text-text-secondary">
        <div class="info-item">
          <span class="label">Conversations:</span>
          <span class="value dark:text-text-primary">{{ storageInfo.conversations }}</span>
        </div>
        <div class="info-item">
          <span class="label">Max conversations:</span>
          <span class="value dark:text-text-primary">{{ limits.MAX_CONVERSATIONS }}</span>
        </div>
        <div class="info-item">
          <span class="label">Max messages/chat:</span>
          <span class="value dark:text-text-primary">{{ limits.MAX_MESSAGES_PER_CONVERSATION }}</span>
        </div>
        <div class="info-item">
          <span class="label">Auto-delete after:</span>
          <span class="value dark:text-text-primary">{{ limits.AUTO_CLEANUP_DAYS }} days</span>
        </div>
      </div>

      <!-- Actions -->
      <div class="actions">
        <button
          v-if="isDangerThreshold"
          @click="handleCleanup"
          class="action-btn cleanup-btn"
          :disabled="loading"
        >
          <i class="fa fa-broom mr-1"></i>
          Cleanup Old Chats
        </button>

        <button
          @click="handleExport"
          class="action-btn export-btn"
          :disabled="loading"
        >
          <i class="fa fa-download mr-1"></i>
          Export
        </button>

        <button
          @click="showClearConfirm = true"
          class="action-btn danger-btn"
          :disabled="loading"
        >
          <i class="fa fa-trash mr-1"></i>
          Clear All
        </button>
      </div>

      <!-- Clear confirmation -->
      <div v-if="showClearConfirm" class="confirm-dialog dark:bg-surface dark:border-border-medium">
        <p class="text-sm mb-3 dark:text-text-primary">
          Are you sure you want to clear all chat history? This cannot be undone.
        </p>
        <div class="confirm-actions">
          <button @click="showClearConfirm = false" class="action-btn cancel-btn">
            Cancel
          </button>
          <button @click="handleClearAll" class="action-btn danger-btn">
            Yes, Clear All
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useStorageQuota } from '@/composables/useStorageQuota'
import { chatHistoryManager } from '@/services/chatHistoryManager.service'
import { ElMessage } from 'element-plus'

const emit = defineEmits(['cleanup', 'clear'])

const {
  storageInfo,
  isWarningThreshold,
  isDangerThreshold,
  isNearFull,
  statusColor,
  statusMessage,
  performCleanup,
  clearAll,
  exportHistory
} = useStorageQuota()

const expanded = ref(false)
const loading = ref(false)
const showClearConfirm = ref(false)

const limits = chatHistoryManager.getLimits()

/**
 * Handle cleanup
 */
async function handleCleanup() {
  loading.value = true
  try {
    const result = await performCleanup()
    if (result.success) {
      ElMessage.success(result.message)
      emit('cleanup')
    } else {
      ElMessage.error(result.message)
    }
  } finally {
    loading.value = false
  }
}

/**
 * Handle clear all
 */
async function handleClearAll() {
  loading.value = true
  showClearConfirm.value = false
  try {
    const result = await clearAll()
    if (result.success) {
      ElMessage.success(result.message)
      emit('clear')
      expanded.value = false
    } else {
      ElMessage.error(result.message)
    }
  } finally {
    loading.value = false
  }
}

/**
 * Handle export
 */
function handleExport() {
  const result = exportHistory()
  if (result.success) {
    ElMessage.success(result.message)
  } else {
    ElMessage.error(result.message)
  }
}
</script>

<style scoped>
.storage-quota-indicator {
  position: relative;
}

.compact-indicator {
  display: flex;
  align-items: center;
  padding: 0.25rem 0.5rem;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.75rem;
}

.compact-indicator:hover {
  opacity: 0.8;
}

.status-success {
  background-color: rgba(34, 197, 94, 0.1);
  color: #22c55e;
}

.status-info {
  background-color: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.status-warning {
  background-color: rgba(251, 191, 36, 0.1);
  color: #fbbf24;
}

.status-error {
  background-color: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.expanded-view {
  position: absolute;
  bottom: 100%;
  right: 0;
  margin-bottom: 0.5rem;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 1rem;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  min-width: 300px;
  max-width: 400px;
  z-index: 50;
}

.dark .expanded-view {
  border-color: var(--border-medium);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.close-btn {
  padding: 0.25rem;
  color: #6b7280;
  transition: color 0.2s;
}

.close-btn:hover {
  color: #1f2937;
}

.dark .close-btn {
  color: var(--text-secondary);
}

.dark .close-btn:hover {
  color: var(--text-primary);
}

.progress-container {
  margin-bottom: 0.75rem;
}

.progress-bar {
  height: 8px;
  background-color: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.25rem;
}

.dark .progress-bar {
  background-color: var(--border-medium);
}

.progress-fill {
  height: 100%;
  transition: width 0.3s;
}

.bg-success {
  background-color: #22c55e;
}

.bg-info {
  background-color: #3b82f6;
}

.bg-warning {
  background-color: #fbbf24;
}

.bg-error {
  background-color: #ef4444;
}

.progress-text {
  color: #6b7280;
  text-align: right;
}

.status-message {
  padding: 0.5rem;
  border-radius: 0.375rem;
  margin-bottom: 0.75rem;
  background-color: rgba(59, 130, 246, 0.05);
}

.text-success {
  color: #22c55e;
}

.text-info {
  color: #3b82f6;
}

.text-warning {
  color: #fbbf24;
}

.text-error {
  color: #ef4444;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  padding: 0.5rem;
  background-color: #f9fafb;
  border-radius: 0.375rem;
}

.dark .info-grid {
  background-color: var(--surface);
}

.info-item {
  display: flex;
  justify-content: space-between;
}

.info-item .label {
  color: #6b7280;
}

.info-item .value {
  font-weight: 500;
}

.actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.action-btn {
  flex: 1;
  padding: 0.375rem 0.75rem;
  font-size: 0.75rem;
  border-radius: 0.375rem;
  border: 1px solid;
  transition: all 0.2s;
  min-width: 80px;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.cleanup-btn {
  background-color: #3b82f6;
  border-color: #3b82f6;
  color: white;
}

.cleanup-btn:hover:not(:disabled) {
  background-color: #2563eb;
}

.export-btn {
  background-color: white;
  border-color: #d1d5db;
  color: #374151;
}

.export-btn:hover:not(:disabled) {
  background-color: #f3f4f6;
}

.dark .export-btn {
  background-color: var(--surface-elevated);
  border-color: var(--border-medium);
  color: var(--text-primary);
}

.dark .export-btn:hover:not(:disabled) {
  background-color: var(--surface);
}

.danger-btn {
  background-color: white;
  border-color: #ef4444;
  color: #ef4444;
}

.danger-btn:hover:not(:disabled) {
  background-color: #ef4444;
  color: white;
}

.cancel-btn {
  background-color: white;
  border-color: #d1d5db;
  color: #374151;
}

.cancel-btn:hover {
  background-color: #f3f4f6;
}

.confirm-dialog {
  margin-top: 0.75rem;
  padding: 0.75rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.375rem;
  background-color: #fef2f2;
}

.confirm-actions {
  display: flex;
  gap: 0.5rem;
}
</style>
