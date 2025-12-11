<!--
  Dashboard View (Refactored)

  Main dashboard container with chat interface.
  Components have been extracted for better performance and maintainability.
-->
<template>
  <div class="workspace-wrapper">
    <div class="workspace-container theme-transition">
      <!-- Left Sidebar -->
      <aside
        id="sidebar"
        class="sidebar bg-white dark:bg-surface border-r border-gray-200 dark:border-border-light flex flex-col theme-transition"
        :class="{ 'sidebar-collapsed': sidebarCollapsed }"
      >
        <!-- Conversation List -->
        <ConversationList
          :chats="chatHistory"
          :current-chat-id="currentChat?.id"
          v-model:search-term="searchTerm"
          @new-chat="handleNewChat"
          @select-chat="selectChat"
          @delete-chat="deleteChat"
          @edit-title="handleEditTitle"
        />

        <!-- Sidebar Footer -->
        <div class="sidebar-footer p-3 border-t border-gray-200 dark:border-border-light bg-white dark:bg-surface flex-shrink-0">
          <div class="flex items-center justify-between text-sm">
            <button
              @click="handleLogout"
              class="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 transition-colors flex items-center gap-1 theme-transition"
            >
              <i class="fa fa-sign-out text-xs"></i>
              <span>Logout</span>
            </button>

            <button
              @click="showConfigurationModal = true"
              class="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 transition-colors flex items-center gap-1 theme-transition"
            >
              <i class="fa fa-cog text-xs"></i>
              <span>Settings</span>
            </button>

            <button
              @click="toggleTheme"
              class="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 transition-colors theme-transition"
            >
              <i class="fa fa-moon-o dark:hidden text-xs"></i>
              <i class="fa fa-sun-o hidden dark:inline text-xs"></i>
            </button>

            <button
              @click="sidebarCollapsed = !sidebarCollapsed"
              class="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 transition-colors theme-transition"
            >
              <i class="fa text-xs" :class="sidebarCollapsed ? 'fa-chevron-right' : 'fa-chevron-left'"></i>
            </button>
          </div>
        </div>
      </aside>

      <!-- Main Content Area -->
      <main class="main-content flex flex-col dark:text-text-primary">
        <!-- Chat Area -->
        <div
          id="chat-container"
          ref="chatContainer"
          class="chat-area p-4 md:p-6 space-y-4 compact-chat theme-transition dark:text-text-primary scrollbar-thin"
        >
          <ChatMessages
            :messages="currentMessages"
            :is-dark="isDark"
            @file-upload="handleFileUpload"
            @file-drop="handleFileDrop"
            @scroll-to-bottom="scrollToBottom"
            @question-clicked="handleQuestionClick"
          />
        </div>

        <!-- Upload Status Bar -->
        <UploadStatusBar
          v-if="isUploadingDocument"
          :file-name="uploadingFileName"
          :progress="uploadProgress"
        />

        <!-- Input Area -->
        <ChatInput
          v-model="userInput"
          :is-dark="isDark"
          :is-recording-voice="isRecordingVoice"
          :is-loading="chatStore.loading"
          :is-uploading-document="isUploadingDocument"
          @send-message="sendMessage"
          @show-prompt-assistance="showPromptAssistanceModal = true"
          @toggle-voice="handleToggleVoice"
        />
      </main>
    </div>

    <!-- Configuration Modal -->
    <ConfigurationPanel
      v-if="showConfigurationModal"
      @close="showConfigurationModal = false"
    />

    <!-- Instruction Assistant Modal -->
    <InstructionAssistant
      v-if="showPromptAssistanceModal"
      @close="showPromptAssistanceModal = false"
      @select="handlePromptSelection"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'
import { useChatManagement } from '@/composables/useChatManagement'
import { useTheme } from '@/composables/useTheme'
import { useVoiceInput } from '@/composables/useVoiceInput'
import ConversationList from '@/components/dashboard/ConversationList.vue'
import ChatMessages from '@/components/dashboard/ChatMessages.vue'
import ChatInput from '@/components/dashboard/ChatInput.vue'
import UploadStatusBar from '@/components/UploadStatusBar.vue'
import ConfigurationPanel from '@/components/ConfigurationPanel.vue'
import InstructionAssistant from '@/components/InstructionAssistant.vue'
import storage from '@/services/storage.service'
import { API_URLS } from '@/config/endpoints'
import { ErrorHandler } from '@/utils/errorHandler'
import { ElMessage } from 'element-plus'

// Import shared styles
import '@/styles/dashboard.css'

const router = useRouter()
const authStore = useAuthStore()
const chatStore = useChatStore()

// Use composables
const {
  currentChat,
  searchTerm,
  filteredChats,
  currentMessages,
  hasMessages,
  createNewChat,
  selectChat,
  deleteChat,
  generateChatTitle,
  addMessage,
  updateLastMessage,
  startEditTitle,
  saveEditedTitle
} = useChatManagement()

const { isDark, toggleTheme } = useTheme()

const {
  isRecordingVoice,
  toggleVoiceInput,
  isVoiceSupported
} = useVoiceInput()

// Local state
const userInput = ref('')
const sidebarCollapsed = ref(false)
const showConfigurationModal = ref(false)
const showPromptAssistanceModal = ref(false)
const chatContainer = ref(null)

// Document upload state
const isUploadingDocument = ref(false)
const uploadingFileName = ref('')
const uploadProgress = ref(0)
const pendingConversationId = ref(null)
const uploadedFilesCount = ref(0)

// Chat history (loaded from storage)
const chatHistory = ref([])

/**
 * Load chat history from storage
 */
function loadChatsFromLocalStorage() {
  try {
    const saved = storage.get('chat-history')
    if (saved) {
      chatHistory.value = saved.map(chat => ({
        ...chat,
        messages: chat.messages.map(msg => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        }))
      }))
    }
  } catch (error) {
    ErrorHandler.logError(error, 'Dashboard.loadChatsFromLocalStorage')
  }
}

/**
 * Save chat history to storage
 */
function saveChatsToLocalStorage() {
  try {
    storage.set('chat-history', chatHistory.value)
  } catch (error) {
    ErrorHandler.logError(error, 'Dashboard.saveChatsToLocalStorage')
  }
}

/**
 * Handle new chat creation
 */
async function handleNewChat() {
  currentChat.value = null
  userInput.value = ''
  searchTerm.value = ''
  showPromptAssistanceModal.value = false
  pendingConversationId.value = null
  uploadedFilesCount.value = 0

  // Reset chat store
  chatStore.instructionMode = false
  chatStore.messages = []
  chatStore.loading = false

  await nextTick()
  scrollToBottom()

  showNotification('New chat started with isolated document context')
}

/**
 * Handle title editing
 */
async function handleEditTitle({ chat, newTitle }) {
  try {
    await saveEditedTitle(chat, newTitle)
    saveChatsToLocalStorage()
    showNotification('Title updated')
  } catch (error) {
    showNotification('Failed to update title', 'error')
  }
}

/**
 * Send message
 */
async function sendMessage(message) {
  if (!message || !message.trim()) return

  try {
    // Create new chat if needed
    if (!currentChat.value) {
      const newChat = {
        id: Date.now(),
        title: 'New Chat',
        messages: [],
        created_at: new Date().toISOString(),
        isGeneratingTitle: false
      }
      chatHistory.value.unshift(newChat)
      currentChat.value = newChat
    }

    // Add user message
    const userMessage = {
      id: Date.now(),
      sender: 'user',
      content: message,
      timestamp: new Date()
    }

    currentChat.value.messages.push(userMessage)
    userInput.value = ''

    // Scroll to bottom
    await nextTick()
    scrollToBottom()

    // Get AI response
    chatStore.loading = true

    const response = await chatStore.sendMessage(
      message,
      pendingConversationId.value
    )

    // Add AI response
    const aiMessage = {
      id: Date.now() + 1,
      sender: 'ai',
      content: response.response || response,
      timestamp: new Date()
    }

    currentChat.value.messages.push(aiMessage)

    // Generate title if this is the first message
    if (currentChat.value.messages.length === 2) {
      currentChat.value.isGeneratingTitle = true
      const title = await generateChatTitle(currentChat.value, message, aiMessage.content)
      currentChat.value.title = title
      currentChat.value.isGeneratingTitle = false
    }

    // Save to storage
    saveChatsToLocalStorage()

    // Scroll to bottom
    await nextTick()
    scrollToBottom()
  } catch (error) {
    const appError = ErrorHandler.handleApiError(error)
    showNotification(ErrorHandler.getUserMessage(appError), 'error')
  } finally {
    chatStore.loading = false
  }
}

/**
 * Handle voice input toggle
 */
async function handleToggleVoice() {
  try {
    if (!isVoiceSupported.value) {
      showNotification('Voice input is not supported in this browser', 'warning')
      return
    }

    const transcribedText = await toggleVoiceInput()

    if (transcribedText) {
      userInput.value = transcribedText
      showNotification('Voice transcribed successfully')
    }
  } catch (error) {
    ErrorHandler.logError(error, 'Dashboard.handleToggleVoice')
    showNotification('Failed to process voice input', 'error')
  }
}

/**
 * Handle file upload
 */
async function handleFileUpload(files) {
  // File upload logic here
  console.log('Files uploaded:', files)
}

/**
 * Handle file drop
 */
async function handleFileDrop(files) {
  // File drop logic here
  console.log('Files dropped:', files)
}

/**
 * Handle question click from suggested questions
 * Fills the input with the clicked question
 */
function handleQuestionClick(question) {
  userInput.value = question
  // Auto-scroll to input area
  nextTick(() => {
    const inputElement = document.querySelector('textarea')
    if (inputElement) {
      inputElement.focus()
      inputElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  })
}

/**
 * Handle prompt selection from assistant
 */
function handlePromptSelection(prompt) {
  userInput.value = prompt
  showPromptAssistanceModal.value = false
}

/**
 * Scroll chat to bottom
 */
function scrollToBottom() {
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

/**
 * Handle logout
 */
function handleLogout() {
  authStore.logout()
  router.push('/login')
}

/**
 * Show notification
 */
function showNotification(message, type = 'success') {
  ElMessage({
    message,
    type,
    duration: 3000
  })
}

// Initialize on mount
onMounted(() => {
  loadChatsFromLocalStorage()
})
</script>

<style scoped>
/* Component-specific styles only - shared styles are in dashboard.css */
</style>
