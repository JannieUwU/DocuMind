<template>
  <div class="ai-message-toolbar" :style="toolbarStyle">
    <div class="toolbar-buttons">
      <!-- Copy按钮 -->
      <button
        class="toolbar-btn"
        :class="{ 'copied': isCopied }"
        :style="buttonStyle"
        @click="handleCopy"
        @mouseenter="hoveredButton = 'copy'"
        @mouseleave="hoveredButton = null"
      >
        <i :class="isCopied ? 'fa fa-check' : 'fa fa-copy'"></i>
        <span>{{ isCopied ? 'Copied' : 'Copy' }}</span>
      </button>

      <!-- Regenerate按钮 -->
      <button
        class="toolbar-btn"
        :style="buttonStyle"
        @click="handleRegenerate"
        @mouseenter="hoveredButton = 'regenerate'"
        @mouseleave="hoveredButton = null"
        :disabled="isRegenerating"
      >
        <i :class="isRegenerating ? 'fa fa-spinner fa-spin' : 'fa fa-refresh'"></i>
        <span>{{ isRegenerating ? 'Generating...' : 'Regenerate' }}</span>
      </button>

      <!-- 提取学术词按钮 -->
      <button
        class="toolbar-btn"
        :style="buttonStyle"
        @click="handleExtractTerms"
        @mouseenter="hoveredButton = 'terms'"
        @mouseleave="hoveredButton = null"
      >
        <i class="fa fa-book"></i>
        <span>Extract Terms</span>
      </button>
    </div>

    <!-- 历史版本指示器 -->
    <div v-if="versionCount > 1" class="version-indicator" :style="versionStyle">
      <button
        class="version-btn"
        @click="$emit('show-history')"
        :style="versionButtonStyle"
      >
        <i class="fa fa-history"></i>
        <span>{{ versionCount }} 个版本</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  messageContent: {
    type: String,
    required: true
  },
  messageId: {
    type: String,
    required: true
  },
  isDark: {
    type: Boolean,
    default: false
  },
  isRegenerating: {
    type: Boolean,
    default: false
  },
  versionCount: {
    type: Number,
    default: 1
  }
})

const emit = defineEmits(['copy', 'regenerate', 'extract-terms', 'show-history'])

const isCopied = ref(false)
const hoveredButton = ref(null)

// 样式计算
const toolbarStyle = computed(() => ({
  backgroundColor: props.isDark ? 'rgba(31, 41, 55, 0.5)' : 'rgba(249, 250, 251, 0.8)',
  borderColor: props.isDark ? 'rgba(75, 85, 99, 0.3)' : 'rgba(229, 231, 235, 0.5)',
  backdropFilter: 'blur(8px)'
}))

const buttonStyle = computed(() => ({
  color: props.isDark ? '#F9FAFB' : '#1F2937',
  borderColor: props.isDark ? 'rgba(75, 85, 99, 0.5)' : 'rgba(229, 231, 235, 0.8)'
}))

const versionStyle = computed(() => ({
  backgroundColor: props.isDark ? 'rgba(59, 130, 246, 0.1)' : 'rgba(59, 130, 246, 0.05)',
  borderColor: props.isDark ? 'rgba(96, 165, 250, 0.3)' : 'rgba(59, 130, 246, 0.2)'
}))

const versionButtonStyle = computed(() => ({
  color: props.isDark ? '#60A5FA' : '#3B82F6'
}))

// Copy功能
const handleCopy = async () => {
  try {
    await navigator.clipboard.writeText(props.messageContent)
    isCopied.value = true
    emit('copy')

    setTimeout(() => {
      isCopied.value = false
    }, 2000)
  } catch (error) {
    console.error('CopyFailed:', error)
  }
}

// Regenerate功能
const handleRegenerate = () => {
  if (!props.isRegenerating) {
    emit('regenerate')
  }
}

// 提取学术词功能
const handleExtractTerms = () => {
  emit('extract-terms', props.messageContent)
}
</script>

<style scoped>
.ai-message-toolbar {
  margin-top: 12px;
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  transition: all 0.3s ease;
}

.toolbar-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.toolbar-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: 1px solid;
  border-radius: 6px;
  background: transparent;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.toolbar-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  background: rgba(59, 130, 246, 0.1);
}

.toolbar-btn:active:not(:disabled) {
  transform: translateY(0);
}

.toolbar-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.toolbar-btn.copied {
  background: rgba(34, 197, 94, 0.1);
  border-color: rgba(34, 197, 94, 0.3);
  color: #22C55E;
}

.toolbar-btn i {
  font-size: 14px;
}

.version-indicator {
  padding: 4px 10px;
  border-radius: 6px;
  border: 1px solid;
  font-size: 12px;
}

.version-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 12px;
  padding: 0;
  transition: opacity 0.2s ease;
}

.version-btn:hover {
  opacity: 0.8;
}

.version-btn i {
  font-size: 12px;
}

/* 响应式设计 */
@media (max-width: 640px) {
  .ai-message-toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .toolbar-buttons {
    width: 100%;
  }

  .toolbar-btn {
    flex: 1;
    justify-content: center;
  }

  .version-indicator {
    width: 100%;
    text-align: center;
  }

  .version-btn {
    width: 100%;
    justify-content: center;
  }
}

/* 动画 */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-5px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.ai-message-toolbar {
  animation: fadeIn 0.3s ease;
}
</style>
