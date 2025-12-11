<!--
  ChatMessage Component

  Displays a single chat message with proper styling and markdown rendering.
-->
<template>
  <div
    :class="`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`"
  >
    <div
      :class="`max-w-2xl w-full theme-transition`"
    >
      <div
        :class="`p-3 rounded-lg text-sm ${
          message.sender === 'user'
            ? 'bg-primary text-white'
            : 'border'
        }`"
        :style="messageStyle"
      >
        <div class="flex items-start gap-2">
          <!-- AI Avatar -->
          <div
            v-if="message.sender === 'ai'"
            class="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center bg-primary/10 text-primary text-xs"
            :style="avatarStyle"
          >
            <i class="fa fa-robot"></i>
          </div>

          <!-- Message Content -->
          <div class="flex-1 min-w-0">
            <!-- AI message with markdown -->
            <div
              v-if="message.sender === 'ai'"
              class="break-words markdown-content"
              :style="contentStyle"
              v-html="renderedContent"
            ></div>

            <!-- User message (plain text) -->
            <p
              v-else
              class="break-words"
              :style="contentStyle"
            >{{ message.content }}</p>

            <!-- Timestamp -->
            <p
              class="text-xs opacity-70 mt-1"
              :style="timestampStyle"
            >{{ formatTime(message.timestamp) }}</p>
          </div>

          <!-- User Avatar -->
          <div
            v-if="message.sender === 'user'"
            class="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-primary text-xs"
            :style="userAvatarStyle"
          >
            <i class="fa fa-user"></i>
          </div>
        </div>
      </div>

      <!-- AI Message Toolbar - Only show when message is complete -->
      <AiMessageToolbar
        v-if="message.sender === 'ai' && message.isComplete !== false"
        :message-content="message.content"
        :message-id="message.id || `msg-${message.timestamp}`"
        :is-dark="isDark"
        :is-regenerating="isRegenerating"
        :version-count="versionCount"
        @copy="handleCopy"
        @regenerate="handleRegenerate"
        @extract-terms="handleExtractTerms"
        @show-history="handleShowHistory"
      />

      <!-- Suggested Questions - Show after AI response toolbar -->
      <div
        v-if="message.sender === 'ai' && message.suggestedQuestions && message.suggestedQuestions.length > 0"
        class="suggested-questions"
      >
        <button
          v-for="(question, qIndex) in message.suggestedQuestions"
          :key="qIndex"
          class="suggested-question-btn"
          :style="getQuestionButtonStyle()"
          @click="handleQuestionClick(question)"
        >
          {{ question }}
        </button>
      </div>
    </div>

    <!-- Academic Terms Modal -->
    <AcademicTermsModal
      :is-visible="showTermsModal"
      :message-content="message.content"
      :is-dark="isDark"
      @close="showTermsModal = false"
      @export-pdf="handleExportPDF"
      @add-to-collection="handleAddToCollection"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { sanitizeMarkdown } from '@/utils/sanitize'
import AiMessageToolbar from '@/components/AiMessageToolbar.vue'
import AcademicTermsModal from '@/components/AcademicTermsModal.vue'

/**
 * @typedef {import('@/types/api.types').ChatMessage} ChatMessage
 */

const props = defineProps({
  /** @type {ChatMessage} */
  message: {
    type: Object,
    required: true
  },
  isDark: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['regenerate', 'show-history', 'question-clicked'])

// Status管理
const showTermsModal = ref(false)
const isRegenerating = ref(false)
const versionCount = ref(1)

// Computed styles based on theme and sender
const messageStyle = computed(() => {
  if (props.message.sender === 'user') {
    return {}
  }
  return props.isDark
    ? {
        backgroundColor: '#1F2937',
        color: '#F9FAFB',
        borderColor: '#4B5563'
      }
    : {
        backgroundColor: '#FFFFFF',
        color: '#1F2937',
        borderColor: '#E5E7EB'
      }
})

const avatarStyle = computed(() => {
  return props.isDark
    ? { backgroundColor: 'rgba(96, 165, 250, 0.2)', color: '#60A5FA' }
    : { backgroundColor: 'rgba(59, 130, 246, 0.1)', color: '#3B82F6' }
})

const userAvatarStyle = computed(() => {
  return props.isDark
    ? { backgroundColor: '#FFFFFF', color: '#60A5FA' }
    : { backgroundColor: '#FFFFFF', color: '#3B82F6' }
})

const contentStyle = computed(() => {
  if (props.message.sender === 'user') {
    return { color: '#FFFFFF' }
  }
  return props.isDark
    ? { color: '#F9FAFB' }
    : { color: '#1F2937' }
})

const timestampStyle = computed(() => {
  if (props.message.sender === 'user') {
    return { color: 'rgba(255, 255, 255, 0.7)' }
  }
  return props.isDark
    ? { color: 'rgba(249, 250, 251, 0.7)' }
    : { color: 'rgba(31, 41, 55, 0.7)' }
})

// Render markdown for AI messages with XSS protection
const renderedContent = computed(() => {
  if (props.message.sender !== 'ai') {
    return props.message.content
  }

  // Use marked library if available
  if (window.marked) {
    const html = window.marked.parse(props.message.content)
    return sanitizeMarkdown(html)
  }

  // Fallback: simple line break conversion with sanitization
  const html = props.message.content.replace(/\n/g, '<br>')
  return sanitizeMarkdown(html)
})

/**
 * Format timestamp
 * @param {string | Date} timestamp - Timestamp to format
 * @returns {string} Formatted time string
 */
function formatTime(timestamp) {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Event handlers for toolbar actions
const handleCopy = () => {
  ElMessage.success('已Copy到剪贴板')
}

const handleRegenerate = async () => {
  isRegenerating.value = true
  try {
    await emit('regenerate', props.message)
    versionCount.value++
  } catch (error) {
    ElMessage.error('RegenerateFailed，请稍后再试')
  } finally {
    // 模拟延迟
    setTimeout(() => {
      isRegenerating.value = false
    }, 1000)
  }
}

const handleExtractTerms = () => {
  showTermsModal.value = true
}

const handleShowHistory = () => {
  emit('show-history', props.message)
}

const handleExportPDF = (terms) => {
  console.log('ExportPDF:', terms)
  ElMessage.success('Export功能开发中...')
}

const handleAddToCollection = (terms) => {
  console.log('添加到收藏:', terms)
  ElMessage.success(`已添加 ${terms.length} 个术语到收藏`)
}

/**
 * Handle clicking on a suggested question
 * Emits the question to parent component to fill the input
 */
const handleQuestionClick = (question) => {
  // Emit event to parent to handle filling the input
  emit('question-clicked', question)
  ElMessage.info('已填充问题到输入框')
}

/**
 * Get button style based on theme
 */
const getQuestionButtonStyle = () => {
  return props.isDark
    ? {
        backgroundColor: '#374151',
        borderColor: '#4B5563',
        color: '#F9FAFB'
      }
    : {
        backgroundColor: '#FFFFFF',
        borderColor: '#E5E7EB',
        color: '#1F2937'
      }
}
</script>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Markdown content styling */
.markdown-content :deep(p) {
  margin-bottom: 0.5rem;
}

.markdown-content :deep(code) {
  background-color: rgba(0, 0, 0, 0.1);
  padding: 0.125rem 0.25rem;
  border-radius: 0.25rem;
  font-family: monospace;
  font-size: 0.875em;
}

.markdown-content :deep(pre) {
  background-color: rgba(0, 0, 0, 0.1);
  padding: 0.75rem;
  border-radius: 0.375rem;
  overflow-x: auto;
  margin: 0.5rem 0;
}

.markdown-content :deep(pre code) {
  background-color: transparent;
  padding: 0;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  margin-left: 1.5rem;
  margin-bottom: 0.5rem;
}

.markdown-content :deep(li) {
  margin-bottom: 0.25rem;
}

.markdown-content :deep(a) {
  color: #60A5FA;
  text-decoration: underline;
}

.markdown-content :deep(a:hover) {
  color: #93C5FD;
}

/* Suggested Questions Styling */
.suggested-questions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 16px;
  width: 100%;
}

.suggested-question-btn {
  border: 1px solid;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 14px;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: normal;
  word-wrap: break-word;
  line-height: 1.5;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.suggested-question-btn:hover {
  border-color: #60A5FA;
  color: #60A5FA;
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(96, 165, 250, 0.2);
}

.suggested-question-btn:active {
  transform: translateY(0);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
</style>
