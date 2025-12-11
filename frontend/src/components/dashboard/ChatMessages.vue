<!--
  ChatMessages Component

  Displays chat messages with markdown rendering support.

  @emits scroll-to-bottom - Emitted when messages are updated (for auto-scroll)
-->
<template>
  <div class="chat-messages space-y-4">
    <!-- Welcome Message -->
    <div v-if="!messages || messages.length === 0" class="flex justify-center items-center h-full">
      <div class="text-center max-w-md">
        <div class="flex flex-col items-center justify-center">
          <!-- Icon -->
          <div class="mb-6 flex justify-center">
            <div class="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
              <i class="fa fa-comment text-2xl text-primary"></i>
            </div>
          </div>

          <!-- Title and subtitle -->
          <h2 class="text-2xl font-bold tracking-tighter xl:text-4xl/none sm:text-3xl mb-3 dark:text-gray-100">
            Hey there 👋
          </h2>
          <span class="text-pretty text-lg tracking-tighter xl:text-2xl/none sm:text-xl text-gray-600 dark:text-gray-300">
            How is it going?
          </span>

          <!-- Description -->
          <p class="mt-4 text-base text-gray-500 dark:text-gray-400 max-w-sm">
            I'm here to help you with any questions you have.
          </p>
        </div>
      </div>
    </div>

    <!-- Message List -->
    <div v-else class="space-y-4">
      <ChatMessage
        v-for="message in messages"
        :key="message.id"
        v-memo="[message.id, message.content, message.sender, message.timestamp]"
        :message="message"
        :is-dark="isDark"
        @render-markdown="renderMarkdown"
        @question-clicked="handleQuestionClick"
      />
    </div>
  </div>
</template>

<script setup>
import { watch, nextTick } from 'vue'
import ChatMessage from './ChatMessage.vue'

/**
 * @typedef {import('@/types/api.types').ChatMessage} ChatMessage
 */

const props = defineProps({
  /** @type {ChatMessage[]} */
  messages: {
    type: Array,
    default: () => []
  },
  isDark: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits([
  'file-upload',
  'file-drop',
  'scroll-to-bottom',
  'question-clicked'
])

// Emit scroll event when messages change
watch(() => props.messages, async () => {
  await nextTick()
  emit('scroll-to-bottom')
}, { deep: true })

/**
 * Handle question click from ChatMessage component
 * Forward the event to the parent
 */
function handleQuestionClick(question) {
  emit('question-clicked', question)
}

/**
 * Render markdown content
 * @param {string} content - Markdown content
 * @returns {string} Rendered HTML
 */
function renderMarkdown(content) {
  // Import marked library if available
  if (window.marked) {
    return window.marked.parse(content)
  }
  // Fallback: simple line break conversion
  return content.replace(/\n/g, '<br>')
}
</script>

<style scoped>
.chat-messages {
  min-height: 100%;
}
</style>
