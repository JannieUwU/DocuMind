<!--
  ChatInput Component

  Chat input area with voice recording, prompt assistance, and file upload support.

  @emits send-message - Emitted when user sends a message
  @emits show-prompt-assistance - Emitted when prompt assistant button is clicked
  @emits toggle-voice - Emitted when voice input is toggled
-->
<template>
  <div class="chat-input border-t border-gray-200 dark:border-border-light p-3 theme-transition bg-white dark:bg-surface">
    <div class="max-w-4xl mx-auto relative">
      <!-- Quick action buttons -->
      <div class="flex justify-center gap-3 mb-3">
        <!-- Stop Generation Button (shows when loading) -->
        <StopGenerationButton v-if="isLoading" />

        <!-- Terms Book Button -->
        <QuickActionButton
          v-if="!isLoading"
          icon="fa-book"
          label="术语词本"
          :is-dark="isDark"
          :badge="termsCount > 0 ? termsCount : null"
          @click="$emit('show-terms-book')"
        />

        <!-- Prompt Assistant Button -->
        <QuickActionButton
          v-if="!isLoading"
          icon="fa-lightbulb-o"
          label="Prompt Assistant"
          :is-dark="isDark"
          @click="$emit('show-prompt-assistance')"
        />

        <!-- Voice Input Button -->
        <QuickActionButton
          v-if="!isLoading"
          :icon="voiceInputIcon"
          :label="isRecordingVoice ? 'Stop Recording' : 'Voice Input'"
          :is-dark="isDark"
          :is-active="isRecordingVoice"
          active-color="#EF4444"
          @click="$emit('toggle-voice')"
        />
      </div>

      <!-- Input form -->
      <form @submit.prevent="handleSubmit" class="flex items-end gap-2">
        <div class="flex-1 relative">
          <textarea
            ref="textareaRef"
            v-model="localInput"
            placeholder="Type a message..."
            class="w-full border border-gray-300 dark:border-gray-600 rounded-lg p-2 pr-8 focus:outline-none focus:ring-2 focus:ring-primary dark:focus:ring-primary resize-none transition-colors dark:bg-gray-800 dark:text-gray-100 text-sm theme-transition placeholder-gray-400 dark:placeholder-gray-500"
            rows="1"
            :maxlength="maxLength"
            @input="handleInput"
            @keydown.ctrl.enter="handleSubmit"
          ></textarea>

          <!-- Character counter -->
          <div class="absolute right-2 top-2 flex gap-1">
            <span class="text-xs text-gray-400 dark:text-gray-400">
              {{ localInput.length }}/{{ maxLength }}
            </span>
          </div>
        </div>

        <!-- Send button -->
        <button
          type="submit"
          class="bg-primary hover:bg-primary/90 text-white dark:text-white rounded-lg p-2 transition-colors flex-shrink-0 theme-transition disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="!canSend"
        >
          <i class="fa fa-paper-plane text-sm text-white"></i>
        </button>
      </form>

      <!-- Shortcuts info -->
      <div class="text-xs text-gray-500 dark:text-gray-400 mt-2 flex items-center justify-between">
        <div class="flex items-center gap-1 dark:text-gray-300">
          <span>Shortcut: </span>
          <kbd class="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-100 rounded text-xs theme-transition">Ctrl</kbd>
          <span>+</span>
          <kbd class="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-100 rounded text-xs theme-transition">Enter</kbd>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useTermsBookStore } from '@/stores/termsBook'
import QuickActionButton from './QuickActionButton.vue'
import StopGenerationButton from '../StopGenerationButton.vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  isDark: {
    type: Boolean,
    default: false
  },
  isRecordingVoice: {
    type: Boolean,
    default: false
  },
  isLoading: {
    type: Boolean,
    default: false
  },
  isUploadingDocument: {
    type: Boolean,
    default: false
  },
  maxLength: {
    type: Number,
    default: 1000
  }
})

const emit = defineEmits([
  'update:modelValue',
  'send-message',
  'show-prompt-assistance',
  'show-terms-book',
  'toggle-voice'
])

const textareaRef = ref(null)
const localInput = ref(props.modelValue)

// Store
const termsBookStore = useTermsBookStore()

// 术语Count
const termsCount = computed(() => termsBookStore.currentTermsCount)

// Sync with v-model
watch(() => props.modelValue, (newValue) => {
  localInput.value = newValue
})

watch(localInput, (newValue) => {
  emit('update:modelValue', newValue)
})

// Voice input icon
const voiceInputIcon = computed(() => {
  return props.isRecordingVoice ? 'fa-stop-circle' : 'fa-microphone'
})

// Can send message
const canSend = computed(() => {
  return localInput.value.trim() && !props.isLoading && !props.isUploadingDocument
})

/**
 * Handle textarea input with auto-resize
 */
function handleInput(event) {
  const textarea = event.target
  // Reset height to auto to get the correct scrollHeight
  textarea.style.height = 'auto'
  // Set height based on content, max 200px
  textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px'
}

/**
 * Handle form submission
 */
function handleSubmit() {
  if (canSend.value) {
    emit('send-message', localInput.value.trim())
    localInput.value = ''

    // Reset textarea height
    nextTick(() => {
      if (textareaRef.value) {
        textareaRef.value.style.height = 'auto'
      }
    })
  }
}
</script>

<style scoped>
.chat-input {
  flex-shrink: 0;
}

textarea {
  transition: all 0.3s ease-in-out;
}
</style>
