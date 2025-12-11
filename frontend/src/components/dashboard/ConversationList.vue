<!--
  ConversationList Component

  Displays the list of chat conversations in the sidebar.

  @emits select-chat - Emitted when a chat is selected
  @emits delete-chat - Emitted when a chat is deleted
  @emits edit-title - Emitted when a chat title is edited
-->
<template>
  <div class="conversation-list">
    <!-- Search Bar -->
    <div class="p-3 border-b border-gray-200 dark:border-border-light flex-shrink-0">
      <div class="relative">
        <input
          type="text"
          placeholder="Search conversations..."
          class="w-full pl-9 pr-3 py-2 text-sm rounded-md bg-gray-100 dark:bg-surface-elevated border border-gray-200 dark:border-border-medium focus:outline-none focus:ring-2 focus:ring-primary dark:focus:ring-primary transition-colors theme-transition"
          v-model="localSearchTerm"
        >
        <span class="absolute left-3 top-2.5 text-gray-400 dark:text-text-tertiary text-sm">
          <i class="fa fa-search"></i>
        </span>
      </div>
    </div>

    <!-- New Chat Button -->
    <div class="p-3 flex justify-center flex-shrink-0">
      <button
        class="w-full py-2 px-4 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-md hover:opacity-90 transition-opacity font-medium"
        @click="$emit('new-chat')"
      >
        <i class="fa fa-plus mr-2"></i>
        New Chat
      </button>
    </div>

    <!-- Chat History -->
    <div class="sidebar-content flex-1 overflow-y-auto scrollbar-thin">
      <h2 class="px-3 py-1 text-xs font-semibold text-gray-500 dark:text-text-tertiary uppercase tracking-wider">
        Chat History
      </h2>
      <div class="space-y-1 p-1">
        <ConversationItem
          v-for="chat in filteredChats"
          :key="chat.id"
          v-memo="[chat.id, chat.title, chat.isGeneratingTitle, currentChatId === chat.id, editingChatId === chat.id]"
          :chat="chat"
          :is-active="currentChatId === chat.id"
          :is-editing="editingChatId === chat.id"
          :editing-title="editingTitle"
          @select="$emit('select-chat', chat)"
          @delete="$emit('delete-chat', chat)"
          @start-edit="handleStartEdit"
          @save-edit="handleSaveEdit"
          @cancel-edit="handleCancelEdit"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import ConversationItem from './ConversationItem.vue'

/**
 * @typedef {import('@/types/api.types').ChatConversation} ChatConversation
 */

const props = defineProps({
  /** @type {ChatConversation[]} */
  chats: {
    type: Array,
    required: true
  },
  currentChatId: {
    type: [String, Number],
    default: null
  },
  searchTerm: {
    type: String,
    default: ''
  }
})

const emit = defineEmits([
  'new-chat',
  'select-chat',
  'delete-chat',
  'edit-title',
  'update:searchTerm'
])

// Local state for search
const localSearchTerm = ref(props.searchTerm)

// Sync search term with parent
watch(localSearchTerm, (newValue) => {
  emit('update:searchTerm', newValue)
})

watch(() => props.searchTerm, (newValue) => {
  localSearchTerm.value = newValue
})

// Editing state
const editingChatId = ref(null)
const editingTitle = ref('')

// Filtered chats based on search
const filteredChats = computed(() => {
  if (!localSearchTerm.value.trim()) {
    return props.chats
  }

  const term = localSearchTerm.value.toLowerCase().trim()
  return props.chats.filter(chat =>
    chat.title.toLowerCase().includes(term)
  )
})

function handleStartEdit(chat) {
  editingChatId.value = chat.id
  editingTitle.value = chat.title
}

function handleSaveEdit(chat) {
  if (editingTitle.value.trim() && editingTitle.value !== chat.title) {
    emit('edit-title', { chat, newTitle: editingTitle.value.trim() })
  }
  editingChatId.value = null
  editingTitle.value = ''
}

function handleCancelEdit() {
  editingChatId.value = null
  editingTitle.value = ''
}
</script>

<style scoped>
.conversation-list {
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* Custom scrollbar */
.scrollbar-thin::-webkit-scrollbar {
  width: 3px;
}

.scrollbar-thin::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.dark .scrollbar-thin::-webkit-scrollbar-track {
  background: var(--surface);
}

.scrollbar-thin::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 1px;
}

.dark .scrollbar-thin::-webkit-scrollbar-thumb {
  background: var(--border-medium);
}

.scrollbar-thin::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.dark .scrollbar-thin::-webkit-scrollbar-thumb:hover {
  background: var(--border-strong);
}
</style>
