<template>
  <Transition name="slide-up">
    <div
      v-if="hasFiles"
      class="upload-status-bar fixed bottom-4 right-4 bg-white dark:bg-surface-elevated rounded-lg shadow-2xl border border-gray-200 dark:border-border-medium z-50 overflow-hidden"
      style="width: 380px; max-height: 500px;"
    >
      <!-- 头部 -->
      <div class="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-border-light bg-gray-50 dark:bg-surface">
        <div class="flex items-center gap-2">
          <i
            class="fa text-sm"
            :class="{
              'fa-spinner fa-spin text-primary': isUploading,
              'fa-check-circle text-green-500': !isUploading && successFiles.length === uploadQueue.length && uploadQueue.length > 0,
              'fa-exclamation-circle text-red-500': errorFiles.length > 0 && !isUploading,
              'fa-cloud-upload text-gray-400': !isUploading && pendingFiles.length > 0
            }"
          ></i>
          <span class="text-sm font-medium text-gray-700 dark:text-text-primary">
            {{ statusTitle }}
          </span>
        </div>

        <div class="flex items-center gap-2">
          <!-- 折叠/Expand -->
          <button
            @click="collapsed = !collapsed"
            class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            :title="collapsed ? 'Expand' : '折叠'"
          >
            <i class="fa text-xs" :class="collapsed ? 'fa-chevron-up' : 'fa-chevron-down'"></i>
          </button>

          <!-- Close -->
          <button
            @click="handleClose"
            class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            title="Close"
          >
            <i class="fa fa-times text-xs"></i>
          </button>
        </div>
      </div>

      <!-- 总进度条 -->
      <div
        v-if="isUploading && !collapsed"
        class="px-4 py-2 bg-gray-50 dark:bg-surface border-b border-gray-200 dark:border-border-light"
      >
        <div class="flex items-center justify-between text-xs text-gray-600 dark:text-text-secondary mb-1">
          <span>总进度</span>
          <span>{{ totalProgress }}%</span>
        </div>
        <div class="w-full h-1.5 bg-gray-200 dark:bg-surface-elevated rounded-full overflow-hidden">
          <div
            class="h-full bg-primary transition-all duration-300"
            :style="{ width: `${totalProgress}%` }"
          ></div>
        </div>
      </div>

      <!-- File List -->
      <div
        v-if="!collapsed"
        class="overflow-y-auto scrollbar-thin"
        style="max-height: 320px;"
      >
        <TransitionGroup name="list">
          <div
            v-for="file in uploadQueue"
            :key="file.id"
            class="px-4 py-3 border-b border-gray-100 dark:border-border-light hover:bg-gray-50 dark:hover:bg-surface transition-colors"
          >
            <div class="flex items-start gap-3">
              <!-- 文件图标 -->
              <div class="flex-shrink-0 mt-0.5">
                <i
                  class="fa fa-file-pdf-o text-lg"
                  :class="{
                    'text-red-500': file.status === 'error',
                    'text-green-500': file.status === 'success',
                    'text-primary': file.status === 'uploading',
                    'text-gray-400': file.status === 'pending'
                  }"
                ></i>
              </div>

              <!-- 文件Information -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center justify-between gap-2 mb-1">
                  <p class="text-sm font-medium text-gray-700 dark:text-text-primary truncate">
                    {{ file.name }}
                  </p>
                  <span class="text-xs text-gray-500 dark:text-text-tertiary whitespace-nowrap">
                    {{ formatFileSize(file.size) }}
                  </span>
                </div>

                <!-- Status -->
                <div class="flex items-center gap-2">
                  <div class="flex-1">
                    <!-- 上传中 -->
                    <div v-if="file.status === 'uploading'">
                      <div class="w-full h-1 bg-gray-200 dark:bg-surface-elevated rounded-full overflow-hidden">
                        <div
                          class="h-full bg-primary transition-all duration-300"
                          :style="{ width: `${file.progress}%` }"
                        ></div>
                      </div>
                      <p class="text-xs text-gray-500 dark:text-text-tertiary mt-1">
                        上传中... {{ file.progress }}%
                      </p>
                    </div>

                    <!-- Success -->
                    <p v-else-if="file.status === 'success'" class="text-xs text-green-600 dark:text-green-400">
                      <i class="fa fa-check"></i> Upload successful
                    </p>

                    <!-- Failed -->
                    <p v-else-if="file.status === 'error'" class="text-xs text-red-600 dark:text-red-400">
                      <i class="fa fa-times"></i> {{ file.error || 'Upload failed' }}
                    </p>

                    <!-- 待上传 -->
                    <p v-else class="text-xs text-gray-500 dark:text-text-tertiary">
                      等待上传...
                    </p>
                  </div>

                  <!-- Actions按钮 -->
                  <button
                    v-if="file.status !== 'uploading'"
                    @click="removeFile(file.id)"
                    class="text-gray-400 hover:text-red-500 dark:hover:text-red-400 transition-colors"
                    title="移除"
                  >
                    <i class="fa fa-trash-o text-xs"></i>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </TransitionGroup>
      </div>

      <!-- 底部Actions -->
      <div
        v-if="!collapsed"
        class="px-4 py-3 bg-gray-50 dark:bg-surface border-t border-gray-200 dark:border-border-light flex items-center justify-between gap-2"
      >
        <div class="text-xs text-gray-600 dark:text-text-secondary">
          {{ uploadQueue.length }} 个文件
          <span v-if="successFiles.length > 0" class="text-green-600 dark:text-green-400">
            ({{ successFiles.length }} Success)
          </span>
          <span v-if="errorFiles.length > 0" class="text-red-600 dark:text-red-400">
            ({{ errorFiles.length }} Failed)
          </span>
        </div>

        <div class="flex items-center gap-2">
          <!-- 重试Failed -->
          <button
            v-if="errorFiles.length > 0 && !isUploading"
            @click="retryFailed"
            class="px-3 py-1 text-xs bg-yellow-500 hover:bg-yellow-600 text-white rounded transition-colors"
          >
            <i class="fa fa-refresh"></i> 重试Failed
          </button>

          <!-- 开始上传 -->
          <button
            v-if="canUpload"
            @click="uploadAll"
            class="px-3 py-1 text-xs bg-primary hover:bg-blue-600 text-white rounded transition-colors"
          >
            <i class="fa fa-cloud-upload"></i> 开始上传
          </button>

          <!-- Clear -->
          <button
            v-if="!isUploading"
            @click="clearCompleted"
            class="px-3 py-1 text-xs bg-gray-500 hover:bg-gray-600 text-white rounded transition-colors"
          >
            Clear
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useFileUpload } from '@/composables/useFileUpload'

const {
  uploadQueue,
  isUploading,
  pendingFiles,
  successFiles,
  errorFiles,
  totalProgress,
  hasFiles,
  canUpload,
  formatFileSize,
  removeFile,
  clearQueue,
  uploadAll,
  retryFailed
} = useFileUpload()

const collapsed = ref(false)

const statusTitle = computed(() => {
  if (isUploading.value) {
    return `Uploading (${uploadQueue.value.findIndex(f => f.status === 'uploading') + 1}/${uploadQueue.value.length})`
  }

  if (errorFiles.value.length > 0 && successFiles.value.length === 0) {
    return 'Upload failed'
  }

  if (successFiles.value.length === uploadQueue.value.length && uploadQueue.value.length > 0) {
    return '全部Upload successful'
  }

  if (successFiles.value.length > 0) {
    return '部分Upload successful'
  }

  return '准备上传'
})

const handleClose = () => {
  if (isUploading.value) {
    if (confirm('Uploading中，确定要Close吗？')) {
      clearQueue()
    }
  } else {
    clearQueue()
  }
}

const clearCompleted = () => {
  clearQueue('success')
}
</script>

<style scoped>
/* 滚动条样式 */
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

/* 过渡动画 */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from {
  transform: translateY(100%);
  opacity: 0;
}

.slide-up-leave-to {
  transform: translateY(20px);
  opacity: 0;
}

.list-enter-active,
.list-leave-active {
  transition: all 0.3s ease;
}

.list-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.list-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

.list-move {
  transition: transform 0.3s ease;
}
</style>
