<template>
  <div class="file-upload-area">
    <!-- 拖拽上传区域 -->
    <div
      class="dropzone"
      :class="{ 'dropzone-active': isDragging, 'has-files': fileList.length > 0 }"
      @drop.prevent="handleDrop"
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @click="triggerFileInput"
    >
      <input
        ref="fileInput"
        type="file"
        accept=".pdf"
        multiple
        class="hidden"
        @change="handleFileSelect"
      />

      <div v-if="fileList.length === 0" class="dropzone-content">
        <div class="icon-wrapper">
          <i class="fa fa-cloud-upload text-4xl text-primary dark:text-blue-400"></i>
        </div>
        <h3 class="text-lg font-semibold text-gray-700 dark:text-text-primary mt-4">
          拖拽 PDF 文件到这里
        </h3>
        <p class="text-sm text-gray-500 dark:text-text-secondary mt-2">
          or click to select文件
        </p>
        <p class="text-xs text-gray-400 dark:text-text-tertiary mt-2">
          支持批量上传，单个文件最大 50MB
        </p>
      </div>

      <!-- File List -->
      <div v-else class="file-list">
        <div class="file-list-header">
          <h4 class="text-sm font-semibold text-gray-700 dark:text-text-primary">
            已选择 {{ fileList.length }} 个文件
          </h4>
          <div class="flex items-center gap-2">
            <button
              @click.stop="triggerFileInput"
              class="text-xs text-primary hover:text-blue-600 dark:text-blue-400 dark:hover:text-blue-300"
            >
              <i class="fa fa-plus"></i> 添加More
            </button>
            <button
              @click.stop="clearAll"
              class="text-xs text-red-500 hover:text-red-600"
            >
              <i class="fa fa-trash-o"></i> 全部清除
            </button>
          </div>
        </div>

        <div class="file-items scrollbar-thin">
          <TransitionGroup name="file-item">
            <div
              v-for="(file, index) in fileList"
              :key="file.id"
              class="file-item"
              :class="{ 'file-item-error': file.status === 'error' }"
            >
              <div class="flex items-center gap-3 flex-1">
                <!-- 序号 -->
                <div class="file-number">
                  {{ index + 1 }}
                </div>

                <!-- PDF图标 -->
                <div class="file-icon">
                  <i class="fa fa-file-pdf-o text-xl text-red-500"></i>
                </div>

                <!-- 文件Information -->
                <div class="file-info flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <p class="file-name truncate">
                      {{ file.name }}
                    </p>
                    <span
                      v-if="file.status === 'success'"
                      class="status-badge status-success"
                    >
                      <i class="fa fa-check"></i> 已上传
                    </span>
                    <span
                      v-else-if="file.status === 'uploading'"
                      class="status-badge status-uploading"
                    >
                      <i class="fa fa-spinner fa-spin"></i> 上传中
                    </span>
                    <span
                      v-else-if="file.status === 'error'"
                      class="status-badge status-error"
                    >
                      <i class="fa fa-times"></i> Failed
                    </span>
                  </div>
                  <div class="flex items-center gap-2 mt-1">
                    <p class="file-size">
                      {{ formatFileSize(file.size) }}
                    </p>
                    <span v-if="file.status === 'uploading'" class="file-progress">
                      {{ file.progress }}%
                    </span>
                  </div>

                  <!-- ErrorInformation -->
                  <p v-if="file.status === 'error' && file.error" class="file-error">
                    {{ file.error }}
                  </p>

                  <!-- 进度条 -->
                  <div
                    v-if="file.status === 'uploading'"
                    class="progress-bar mt-2"
                  >
                    <div
                      class="progress-fill"
                      :style="{ width: `${file.progress}%` }"
                    ></div>
                  </div>
                </div>
              </div>

              <!-- Delete按钮 -->
              <button
                v-if="file.status !== 'uploading'"
                @click.stop="removeFile(file.id)"
                class="delete-btn"
                title="移除文件"
              >
                <i class="fa fa-times"></i>
              </button>
            </div>
          </TransitionGroup>
        </div>

        <!-- 批量Actions -->
        <div class="file-list-footer">
          <button
            v-if="canUpload"
            @click.stop="startUpload"
            class="upload-btn"
          >
            <i class="fa fa-cloud-upload"></i>
            开始上传 ({{ pendingFiles.length }})
          </button>

          <button
            v-if="errorFiles.length > 0"
            @click.stop="retryFailed"
            class="retry-btn"
          >
            <i class="fa fa-refresh"></i>
            重试Failed ({{ errorFiles.length }})
          </button>
        </div>
      </div>
    </div>

    <!-- ErrorTips -->
    <Transition name="fade">
      <div
        v-if="errorMessage"
        class="error-toast"
      >
        <i class="fa fa-exclamation-circle"></i>
        {{ errorMessage }}
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useFileUpload, type UploadFile } from '@/composables/useFileUpload'

interface Props {
  conversationId?: number
}

const props = defineProps<Props>()

const emit = defineEmits<{
  uploaded: [file: UploadFile]
  error: [error: string]
}>()

const {
  uploadQueue,
  pendingFiles,
  errorFiles,
  canUpload,
  formatFileSize,
  addFiles,
  removeFile: removeFileFromQueue,
  clearQueue,
  uploadAll,
  retryFailed: retryFailedUpload
} = useFileUpload()

const fileInput = ref<HTMLInputElement>()
const isDragging = ref(false)
const errorMessage = ref('')

// 使用 uploadQueue 作为File List
const fileList = computed(() => uploadQueue.value)

const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    addFilesToQueue(target.files)
    target.value = '' // Clear input，允许重复选择相同文件
  }
}

const handleDrop = (event: DragEvent) => {
  isDragging.value = false

  if (event.dataTransfer?.files) {
    addFilesToQueue(event.dataTransfer.files)
  }
}

const addFilesToQueue = (files: FileList) => {
  const result = addFiles(files, props.conversationId)

  if (result.rejected.length > 0) {
    const errors = result.rejected.map(r => r.reason).join(', ')
    showError(errors)
  }

  if (result.added > 0) {
    showError(`Success添加 ${result.added} 个文件`)
  }
}

const removeFile = (fileId: string) => {
  removeFileFromQueue(fileId)
}

const clearAll = () => {
  if (confirm('确定要清除所有文件吗？')) {
    clearQueue()
  }
}

const startUpload = async () => {
  const result = await uploadAll()

  if (result.success > 0) {
    showError(`Success上传 ${result.success} 个文件`)

    // 通知父组件
    uploadQueue.value
      .filter(f => f.status === 'success')
      .forEach(f => emit('uploaded', f))
  }

  if (result.failed > 0) {
    showError(`${result.failed} 个文件Upload failed`)
    emit('error', `${result.failed} 个文件Upload failed`)
  }
}

const retryFailed = async () => {
  const result = await retryFailedUpload()

  if (result.success > 0) {
    showError(`重试Success: ${result.success} 个文件`)
  }
}

const showError = (message: string) => {
  errorMessage.value = message
  setTimeout(() => {
    errorMessage.value = ''
  }, 3000)
}

// 监听 conversationId 变化，更新队列中的文件
watch(() => props.conversationId, (newId) => {
  uploadQueue.value.forEach(file => {
    if (file.status === 'pending') {
      file.conversationId = newId
    }
  })
})
</script>

<style scoped>
.file-upload-area {
  position: relative;
}

/* 拖拽区域 */
.dropzone {
  border: 2px dashed #e5e7eb;
  border-radius: 12px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: linear-gradient(135deg, #f9fafb 0%, #ffffff 100%);
}

.dark .dropzone {
  border-color: #374151;
  background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
}

.dropzone:hover {
  border-color: #3b82f6;
  background: linear-gradient(135deg, #eff6ff 0%, #ffffff 100%);
}

.dark .dropzone:hover {
  border-color: #60a5fa;
  background: linear-gradient(135deg, #1e3a5f 0%, #1f2937 100%);
}

.dropzone-active {
  border-color: #3b82f6;
  background: linear-gradient(135deg, #dbeafe 0%, #eff6ff 100%);
  transform: scale(1.02);
}

.dark .dropzone-active {
  border-color: #60a5fa;
  background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
}

.dropzone.has-files {
  padding: 20px;
  text-align: left;
}

.dropzone-content {
  pointer-events: none;
}

.icon-wrapper {
  display: inline-block;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

/* File List */
.file-list {
  width: 100%;
}

.file-list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e5e7eb;
}

.dark .file-list-header {
  border-color: #374151;
}

.file-items {
  max-height: 400px;
  overflow-y: auto;
  margin-bottom: 16px;
  padding-right: 8px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  margin-bottom: 8px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.dark .file-item {
  background: #1f2937;
  border-color: #374151;
}

.file-item:hover {
  background: #f9fafb;
  border-color: #d1d5db;
}

.dark .file-item:hover {
  background: #374151;
  border-color: #4b5563;
}

.file-item-error {
  border-color: #f87171;
  background: #fef2f2;
}

.dark .file-item-error {
  border-color: #dc2626;
  background: #4c0f0f;
}

.file-number {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: #e5e7eb;
  color: #6b7280;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 600;
}

.dark .file-number {
  background: #374151;
  color: #9ca3af;
}

.file-icon {
  flex-shrink: 0;
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
}

.dark .file-name {
  color: #f9fafb;
}

.file-size {
  font-size: 12px;
  color: #6b7280;
}

.dark .file-size {
  color: #9ca3af;
}

.file-progress {
  font-size: 12px;
  color: #3b82f6;
  font-weight: 600;
}

.file-error {
  font-size: 12px;
  color: #dc2626;
  margin-top: 4px;
}

/* Status徽章 */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
}

.status-success {
  background: #dcfce7;
  color: #166534;
}

.dark .status-success {
  background: #14532d;
  color: #86efac;
}

.status-uploading {
  background: #dbeafe;
  color: #1e40af;
}

.dark .status-uploading {
  background: #1e3a8a;
  color: #93c5fd;
}

.status-error {
  background: #fee2e2;
  color: #991b1b;
}

.dark .status-error {
  background: #7f1d1d;
  color: #fca5a5;
}

/* 进度条 */
.progress-bar {
  width: 100%;
  height: 4px;
  background: #e5e7eb;
  border-radius: 2px;
  overflow: hidden;
}

.dark .progress-bar {
  background: #374151;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #60a5fa);
  transition: width 0.3s ease;
}

/* Delete按钮 */
.delete-btn {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  color: #9ca3af;
  transition: all 0.2s ease;
}

.delete-btn:hover {
  background: #fee2e2;
  color: #dc2626;
}

.dark .delete-btn:hover {
  background: #7f1d1d;
  color: #f87171;
}

/* 底部Actions */
.file-list-footer {
  display: flex;
  gap: 12px;
  padding-top: 12px;
  border-top: 1px solid #e5e7eb;
}

.dark .file-list-footer {
  border-color: #374151;
}

.upload-btn,
.retry-btn {
  flex: 1;
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.upload-btn {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
}

.upload-btn:hover {
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

.retry-btn {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: white;
}

.retry-btn:hover {
  background: linear-gradient(135deg, #d97706, #b45309);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.4);
}

/* ErrorTips */
.error-toast {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 12px 20px;
  background: #1f2937;
  color: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  z-index: 9999;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

/* 过渡动画 */
.file-item-enter-active,
.file-item-leave-active {
  transition: all 0.3s ease;
}

.file-item-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.file-item-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

.file-item-move {
  transition: transform 0.3s ease;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 滚动条 */
.scrollbar-thin {
  scrollbar-width: thin;
  scrollbar-color: rgba(156, 163, 175, 0.5) transparent;
}

.scrollbar-thin::-webkit-scrollbar {
  width: 6px;
}

.scrollbar-thin::-webkit-scrollbar-track {
  background: transparent;
}

.scrollbar-thin::-webkit-scrollbar-thumb {
  background-color: rgba(156, 163, 175, 0.5);
  border-radius: 3px;
}

.scrollbar-thin::-webkit-scrollbar-thumb:hover {
  background-color: rgba(156, 163, 175, 0.7);
}
</style>
