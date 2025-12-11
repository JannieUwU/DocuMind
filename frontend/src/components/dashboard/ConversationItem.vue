<!--
  ConversationItem Component

  Displays a single conversation item in the sidebar list.

  @emits select - Emitted when the conversation is selected
  @emits delete - Emitted when the conversation is deleted
  @emits start-edit - Emitted when editing starts
  @emits save-edit - Emitted when editing is saved
  @emits cancel-edit - Emitted when editing is cancelled
-->
<template>
  <div
    class="chat-item p-2 rounded-md hover:bg-gray-100 dark:hover:bg-surface-elevated cursor-pointer transition-all text-sm theme-transition"
    :class="{
      'bg-primary/10 dark:bg-primary/20 border-l-2 border-primary': isActive,
      'opacity-50': chat.isGeneratingTitle
    }"
    @click="$emit('select')"
  >
    <div class="flex items-center justify-between gap-1">
      <!-- Editable title -->
      <input
        v-if="isEditing"
        v-model="localEditingTitle"
        @click.stop
        @blur="$emit('save-edit', chat)"
        @keydown.enter="$emit('save-edit', chat)"
        @keydown.esc="$emit('cancel-edit')"
        class="flex-1 mr-1 px-1 py-0.5 text-xs rounded border border-primary dark:border-primary focus:outline-none focus:ring-1 focus:ring-primary bg-white dark:bg-surface-elevated text-gray-800 dark:text-text-primary"
        ref="titleInput"
        autofocus
      />

      <!-- Display title -->
      <span
        v-else
        class="truncate flex-1 mr-2 text-gray-800 dark:text-text-primary flex items-center gap-1"
        @dblclick.stop="$emit('start-edit', chat)"
      >
        <span
          v-if="chat.isGeneratingTitle"
          class="inline-block w-3 h-3 border-2 border-primary border-t-transparent rounded-full animate-spin"
        ></span>
        {{ chat.title }}
      </span>

      <!-- Action buttons -->
      <div class="flex items-center gap-1 flex-shrink-0">
        <button
          v-if="!isEditing"
          @click.stop="$emit('start-edit', chat)"
          class="text-gray-400 hover:text-primary dark:text-gray-400 dark:hover:text-primary text-xs transition-colors theme-transition"
          title="Edit title"
        >
          <i class="fa fa-pencil"></i>
        </button>
        <button
          @click.stop="$emit('delete', chat)"
          class="text-gray-400 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400 text-xs transition-colors theme-transition"
          title="Delete conversation"
        >
          <i class="fa fa-trash-o"></i>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'

/**
 * @typedef {import('@/types/api.types').ChatConversation} ChatConversation
 */

const props = defineProps({
  /** @type {ChatConversation} */
  chat: {
    type: Object,
    required: true
  },
  isActive: {
    type: Boolean,
    default: false
  },
  isEditing: {
    type: Boolean,
    default: false
  },
  editingTitle: {
    type: String,
    default: ''
  }
})

const emit = defineEmits([
  'select',
  'delete',
  'start-edit',
  'save-edit',
  'cancel-edit'
])

const titleInput = ref(null)
const localEditingTitle = ref(props.editingTitle)

// Sync editing title
watch(() => props.editingTitle, (newValue) => {
  localEditingTitle.value = newValue
})

watch(localEditingTitle, (newValue) => {
  emit('update:editingTitle', newValue)
})

// Auto-focus input when editing starts
watch(() => props.isEditing, async (isEditing) => {
  if (isEditing) {
    await nextTick()
    titleInput.value?.focus()
  }
})
</script>

<style scoped>
.chat-item {
  max-height: 2.5rem;
}
</style>
