<template>
  <!-- Fixed-size workspace container - centered on screen -->
  <div class="workspace-wrapper">
    <div class="workspace-container theme-transition">
      <!-- Left Sidebar - Fixed width, full height -->
      <aside id="sidebar" class="sidebar bg-white dark:bg-surface border-r border-gray-200 dark:border-border-light flex flex-col theme-transition" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
        <!-- Search Bar -->
        <div class="p-3 border-b border-gray-200 dark:border-border-light flex-shrink-0">
          <div class="relative">
            <input
              type="text"
              placeholder="Search conversations..."
              class="w-full pl-9 pr-3 py-2 text-sm rounded-md bg-gray-100 dark:bg-surface-elevated border border-gray-200 dark:border-border-medium focus:outline-none focus:ring-2 focus:ring-primary dark:focus:ring-primary transition-colors theme-transition"
              v-model="searchTerm"
            >
            <span class="absolute left-3 top-2.5 text-gray-400 dark:text-text-tertiary text-sm">
              <i class="fa fa-search"></i>
            </span>
          </div>
        </div>

        <!-- New Chat Button with Sparkles Effect -->
        <div class="p-3 flex justify-center flex-shrink-0">
          <SparklesText
            text="New Chat"
            :colors="{ first: '#9E7AFF', second: '#FE8BBB' }"
            :sparkles-count="6"
            class="text-xl my-2 cursor-pointer transform hover:scale-105 transition-transform duration-300"
            @click="newChat"
          />
        </div>

        <!-- Chat History - Scrollable -->
        <div class="sidebar-content flex-1 overflow-y-auto scrollbar-thin">
          <h2 class="px-3 py-1 text-xs font-semibold text-gray-500 dark:text-text-tertiary uppercase tracking-wider">Chat History</h2>
          <div id="chat-history" class="space-y-1 p-1">
            <div
              v-for="chat in filteredChats"
              :key="chat.id"
              class="chat-item p-2 rounded-md hover:bg-gray-100 dark:hover:bg-surface-elevated cursor-pointer transition-all text-sm theme-transition"
              :class="{
                'bg-primary/10 dark:bg-primary/20 border-l-2 border-primary': currentChat?.id === chat.id,
                'opacity-50': chat.isGeneratingTitle
              }"
              @click="selectChat(chat)"
            >
              <div class="flex items-center justify-between gap-1">
                <!-- Editable title -->
                <input
                  v-if="editingChatId === chat.id"
                  v-model="editingChatTitle"
                  @click.stop
                  @blur="saveEditedTitle(chat)"
                  @keydown.enter="saveEditedTitle(chat)"
                  @keydown.esc="cancelEditTitle"
                  class="flex-1 mr-1 px-1 py-0.5 text-xs rounded border border-primary dark:border-primary focus:outline-none focus:ring-1 focus:ring-primary bg-white dark:bg-surface-elevated text-gray-800 dark:text-text-primary"
                  ref="titleInput"
                  autofocus
                />
                <!-- Display title -->
                <span
                  v-else
                  class="truncate flex-1 mr-2 text-gray-800 dark:text-text-primary flex items-center gap-1"
                  @dblclick.stop="startEditTitle(chat)"
                >
                  <span v-if="chat.isGeneratingTitle" class="inline-block w-3 h-3 border-2 border-primary border-t-transparent rounded-full animate-spin"></span>
                  {{ chat.title }}
                </span>

                <!-- Action buttons -->
                <div class="flex items-center gap-1 flex-shrink-0">
                  <button
                    v-if="editingChatId !== chat.id"
                    @click.stop="startEditTitle(chat)"
                    class="text-gray-400 hover:text-primary dark:text-gray-400 dark:hover:text-primary text-xs transition-colors theme-transition"
                    title="Edit title"
                  >
                    <i class="fa fa-pencil"></i>
                  </button>
                  <button
                    @click.stop="deleteChat(chat)"
                    class="text-gray-400 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400 text-xs transition-colors theme-transition"
                    title="Delete conversation"
                  >
                    <i class="fa fa-trash-o"></i>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Sidebar Footer - Fixed at bottom -->
        <div class="sidebar-footer p-3 border-t border-gray-200 dark:border-border-light bg-white dark:bg-surface flex-shrink-0">
          <div class="flex items-center justify-between text-sm">
            <button
              @click="handleLogout"
              class="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 transition-colors flex items-center gap-1 theme-transition"
            >
              <i class="fa fa-sign-out text-xs"></i>
              <span>Logout</span>
            </button>

            <!-- Settings button -->
            <button
              @click="showConfiguration"
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
              @click="toggleSidebar"
              class="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 transition-colors theme-transition"
            >
              <i class="fa text-xs" :class="sidebarCollapsed ? 'fa-chevron-right' : 'fa-chevron-left'"></i>
            </button>
          </div>
        </div>
      </aside>

      <!-- Main Content Area - Fills remaining width -->
      <main class="main-content flex flex-col dark:text-text-primary">
        <!-- Chat Area - Fills available space, scrollable -->
        <div
          id="chat-container"
          class="chat-area p-4 md:p-6 space-y-4 compact-chat theme-transition dark:text-text-primary scrollbar-thin"
        >
        <!-- Welcome Message with BlurReveal Animation -->
        <div v-if="!currentChat" class="flex justify-center items-center h-full">
          <div class="text-center max-w-md">
            <ClientOnly>
              <BlurReveal
                :delay="0.2"
                :duration="0.75"
                class="flex flex-col items-center justify-center"
              >
                <!-- 图标部分 -->
                <div class="mb-6 flex justify-center">
                  <div class="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
                    <i class="fa fa-comment text-2xl text-primary"></i>
                  </div>
                </div>
                
                <!-- Title和副Title -->
                <h2 class="text-2xl font-bold tracking-tighter xl:text-4xl/none sm:text-3xl mb-3 dark:text-gray-100">Hey there 👋</h2>
                <span class="text-pretty text-lg tracking-tighter xl:text-2xl/none sm:text-xl text-gray-600 dark:text-gray-300">
                  How is it going?
                </span>
                
                <!-- Description文本 -->
                <p class="mt-4 text-base text-gray-500 dark:text-gray-400 max-w-sm">
                  I'm here to help you with any questions you have.
                </p>
              </BlurReveal>
            </ClientOnly>
            
            <!-- 文件上传区域 -->
            <div class="mt-8 space-y-4 p-6 dark:bg-transparent">
              <FileUpload
                class="rounded-lg border border-dashed border-neutral-200 dark:border-border-medium dark:text-text-primary"
                @onChange="handleFileUpload"
                @onDrop="handleFileDrop">
                <FileUploadGrid />
              </FileUpload>
            </div>
          </div>
        </div>

        <!-- Chat Messages -->
        <div v-else class="space-y-4">
          <div
            v-for="message in currentChat.messages"
            :key="message.id"
            class="animate-fade-in"
          >
            <div :class="`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`">
              <div
                :class="`max-w-2xl p-3 rounded-lg text-sm theme-transition ${
                  message.sender === 'user'
                    ? 'bg-primary text-white'
                    : 'border'
                }`"
                :style="message.sender === 'user'
                  ? {}
                  : isDark
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
                "
              >
                <div class="flex items-start gap-2">
                  <div
                    v-if="message.sender === 'ai'"
                    class="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center bg-primary/10 text-primary text-xs"
                    :style="isDark
                      ? { backgroundColor: 'rgba(96, 165, 250, 0.2)', color: '#60A5FA' }
                      : { backgroundColor: 'rgba(59, 130, 246, 0.1)', color: '#3B82F6' }
                    "
                  >
                    <i class="fa fa-robot"></i>
                  </div>
                  <div class="flex-1 min-w-0">
                    <!-- AI消息 - 使用段落交互 -->
                    <div v-if="message.sender === 'ai'">
                      <ParagraphInteraction
                        v-for="paragraph in getMessageParagraphs(message)"
                        :key="paragraph.id"
                        :content="paragraph.html"
                        :text="paragraph.text"
                        :source="paragraph.source"
                        :is-dark="isDark"
                        @show-source="handleShowSource"
                        @explain="handleExplainParagraph"
                        @search="handleSearchParagraph"
                      />
                    </div>
                    <!-- 用户消息 -->
                    <p
                      v-else
                      class="break-words"
                      :style="message.sender === 'user'
                        ? { color: '#FFFFFF' }
                        : isDark
                          ? { color: '#F9FAFB' }
                          : { color: '#1F2937' }
                      "
                    >{{ message.content }}</p>
                    <p
                      class="text-xs opacity-70 mt-1"
                      :style="message.sender === 'user'
                        ? { color: 'rgba(255, 255, 255, 0.7)' }
                        : isDark
                          ? { color: 'rgba(249, 250, 251, 0.7)' }
                          : { color: 'rgba(31, 41, 55, 0.7)' }
                      "
                    >{{ formatTime(message.timestamp) }}</p>
                  </div>
                  <div
                    v-if="message.sender === 'user'"
                    class="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-primary text-xs"
                    :style="isDark
                      ? { backgroundColor: '#FFFFFF', color: '#60A5FA' }
                      : { backgroundColor: '#FFFFFF', color: '#3B82F6' }
                    "
                  >
                    <i class="fa fa-user"></i>
                  </div>
                </div>
              </div>
            </div>

            <!-- AI Message Toolbar (only for AI messages that are complete) -->
            <div v-if="message.sender === 'ai' && message.isComplete !== false" class="flex justify-start">
              <div class="max-w-2xl w-full">
                <AiMessageToolbar
                  :message="message"
                  :is-dark="isDark"
                  :version-count="1"
                  @copy="handleCopyMessage(message)"
                  @regenerate="handleRegenerateMessage(message)"
                  @extract-terms="handleExtractTerms(message)"
                />

                <!-- Suggested Questions - Show after toolbar -->
                <div
                  v-if="message.suggestedQuestions && message.suggestedQuestions.length > 0"
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
            </div>
          </div>
        </div>
      </div>

        <!-- Input Area - Fixed height, always at bottom -->
        <div class="input-area border-t border-gray-200 dark:border-border-light p-3 compact-input theme-transition bg-white dark:bg-surface flex-shrink-0">
        <div class="max-w-4xl mx-auto relative">
          <!-- Quick action buttons -->
          <div class="flex justify-center gap-3 mb-3">
            <button
              type="button"
              @click="showTermsBook"
              class="flex items-center gap-1 px-3 py-1.5 rounded-md border transition-colors text-xs theme-transition relative"
              :style="isDark
                ? {
                    borderColor: '#4B5563',
                    color: '#F9FAFB',
                    backgroundColor: 'transparent'
                  }
                : {
                    borderColor: '#D1D5DB',
                    color: '#374151',
                    backgroundColor: 'transparent'
                  }
              "
              @mouseenter="(e) => {
                const btn = e.currentTarget
                if (isDark) {
                  btn.style.backgroundColor = '#374151'
                  btn.style.color = '#F9FAFB'
                  const icon = btn.querySelector('i')
                  if (icon) icon.style.color = '#F9FAFB'
                } else {
                  btn.style.backgroundColor = '#F3F4F6'
                  btn.style.color = '#374151'
                  const icon = btn.querySelector('i')
                  if (icon) icon.style.color = '#374151'
                }
              }"
              @mouseleave="(e) => {
                const btn = e.currentTarget
                btn.style.backgroundColor = 'transparent'
                btn.style.color = isDark ? '#F9FAFB' : '#374151'
                const icon = btn.querySelector('i')
                if (icon) icon.style.color = isDark ? '#F9FAFB' : '#374151'
              }"
            >
              <i
                class="fa fa-book"
                :style="{ color: isDark ? '#F9FAFB' : '#374151' }"
              ></i>
              <span>Terms Book</span>
              <!-- Badge -->
              <span
                v-if="termsCount > 0"
                class="absolute -top-1.5 -right-1.5 min-w-[18px] h-[18px] flex items-center justify-center rounded-full text-[10px] font-semibold px-1 shadow-md"
                style="background-color: #EF4444; color: #FFFFFF;"
              >
                {{ termsCount }}
              </span>
            </button>
            <button
              type="button"
              @click="showPromptAssistance"
              class="flex items-center gap-1 px-3 py-1.5 rounded-md border transition-colors text-xs theme-transition"
              :style="isDark 
                ? { 
                    borderColor: '#4B5563', 
                    color: '#F9FAFB',
                    backgroundColor: 'transparent'
                  }
                : { 
                    borderColor: '#D1D5DB', 
                    color: '#374151',
                    backgroundColor: 'transparent'
                  }
              "
              @mouseenter="(e) => {
                const btn = e.currentTarget
                if (isDark) {
                  btn.style.backgroundColor = '#374151'
                  btn.style.color = '#F9FAFB'
                  const icon = btn.querySelector('i')
                  if (icon) icon.style.color = '#F9FAFB'
                } else {
                  btn.style.backgroundColor = '#F3F4F6'
                  btn.style.color = '#374151'
                  const icon = btn.querySelector('i')
                  if (icon) icon.style.color = '#374151'
                }
              }"
              @mouseleave="(e) => {
                const btn = e.currentTarget
                btn.style.backgroundColor = 'transparent'
                btn.style.color = isDark ? '#F9FAFB' : '#374151'
                const icon = btn.querySelector('i')
                if (icon) icon.style.color = isDark ? '#F9FAFB' : '#374151'
              }"
            >
              <i 
                class="fa fa-lightbulb-o"
                :style="{ color: isDark ? '#F9FAFB' : '#374151' }"
              ></i>
              <span>Prompt Assistant</span>
            </button>
          </div>
          
          <!-- Input form -->
          <form @submit.prevent="sendMessage" class="flex items-end gap-2">
            <div class="flex-1 relative">
              <textarea
                v-model="userInput"
                placeholder="Type a message..."
                class="w-full border border-gray-300 dark:border-gray-600 rounded-lg p-2 pr-8 focus:outline-none focus:ring-2 focus:ring-primary dark:focus:ring-primary resize-none transition-colors dark:bg-gray-800 dark:text-gray-100 text-sm theme-transition placeholder-gray-400 dark:placeholder-gray-500"
                rows="1"
                @input="autoResize"
                @keydown.ctrl.enter="sendMessage"
              ></textarea>
              <div class="absolute right-2 top-2 flex gap-1">
                <span class="text-xs text-gray-400 dark:text-gray-400">{{ userInput.length }}/1000</span>
              </div>
            </div>
            <button
              type="submit"
              class="bg-primary hover:bg-primary/90 text-white dark:text-white rounded-lg p-2 transition-colors flex-shrink-0 theme-transition disabled:opacity-50 disabled:cursor-not-allowed"
              :disabled="!userInput.trim() || chatStore.loading || isUploadingDocument"
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
      </main>
    </div>
  </div>

    <!-- Configuration Modal -->
    <div v-if="showConfigurationModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 animate-fade-in">
      <div 
        class="rounded-lg shadow-xl p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto animate-slide-in theme-transition"
        :style="modalStyle"
      >
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-xl font-bold text-gray-900 dark:text-gray-100">API Configuration</h3>
          <button @click="closeConfiguration" class="text-gray-500 hover:text-gray-700 dark:text-gray-300 dark:hover:text-gray-100 theme-transition">
            <i class="fa fa-times"></i>
          </button>
        </div>
        
        <ConfigurationPanel @close="closeConfiguration" />
      </div>
    </div>

    <!-- 上传进度Status栏 -->
    <UploadStatusBar />

    <!-- Prompt Assistance Modal -->
    <div v-if="showPromptAssistanceModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 animate-fade-in p-4">
      <div
        class="rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden animate-slide-in theme-transition flex flex-col"
        :style="modalStyle"
      >
        <div class="flex justify-between items-center p-4 border-b flex-shrink-0"
          :style="isDark ? { borderColor: '#4B5563' } : { borderColor: '#E5E7EB' }"
        >
          <h3
            class="text-lg font-bold"
            :style="isDark ? { color: '#F9FAFB' } : { color: '#1F2937' }"
          >Prompt Assistant</h3>
          <button
            @click="closePromptAssistance"
            class="theme-transition hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full p-2 transition-colors"
            :style="isDark ? { color: '#D1D5DB' } : { color: '#6B7280' }"
          >
            <i class="fa fa-times"></i>
          </button>
        </div>

        <div class="overflow-y-auto flex-1 p-4">
          <InstructionAssistant @close="closePromptAssistance" />
        </div>
      </div>
    </div>

    <!-- 来源Information模态框 -->
    <SourceInfoModal
      :visible="showSourceModal"
      :source-info="currentSourceInfo"
      :quoted-text="currentQuotedText"
      @close="showSourceModal = false"
      @open-document="handleOpenDocument"
    />

    <!-- 术语词本面板 -->
    <TermsBookPanel
      :is-visible="showTermsBookModal"
      :is-dark="isDark"
      @close="showTermsBookModal = false"
    />

    <!-- 学术词弹窗 -->
    <AcademicTermsModal
      :is-visible="showAcademicTermsModal"
      :message-content="currentMessageForTerms?.content || ''"
      :is-dark="isDark"
      @close="showAcademicTermsModal = false"
    />
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'
import FileUpload from '@/components/FileUpload.vue'
import FileUploadGrid from '@/components/FileUploadGrid.vue'
import UploadStatusBar from '@/components/UploadStatusBar.vue'
import SparklesText from '@/components/SparklesText.vue'
import BlurReveal from '@/components/BlurReveal.vue'
import ClientOnly from '@/components/ClientOnly.vue'
import InstructionAssistant from '@/components/InstructionAssistant.vue'
import ParagraphInteraction from '@/components/ParagraphInteraction.vue'
import SourceInfoModal from '@/components/SourceInfoModal.vue'
import TermsBookPanel from '@/components/TermsBookPanel.vue'
import AiMessageToolbar from '@/components/AiMessageToolbar.vue'
import AcademicTermsModal from '@/components/AcademicTermsModal.vue'
import { ElMessage } from 'element-plus'
import ConfigurationPanel from '@/components/ConfigurationPanel.vue'
import { themeManager } from '@/utils/theme'
import { marked } from 'marked'
import { sanitizeMarkdown } from '@/utils/sanitize'
import { parseHtmlToParagraphs } from '@/utils/paragraphParser'
import storage from '@/services/storage.service'
import secureStorage from '@/services/secureStorage.service'
import titleGenerator from '@/services/titleGenerator.service'
import { useTermsBookStore } from '@/stores/termsBook'
import { API_URLS } from '@/config/endpoints'
import { CHAT_CONFIG, UI_CONFIG } from '@/config/constants'

const router = useRouter()
const authStore = useAuthStore()
const chatStore = useChatStore()
const termsBookStore = useTermsBookStore()

// 响应式主题Status
const currentTheme = ref(themeManager.getCurrentTheme())

// 计算当前主题
const isDark = computed(() => {
  return currentTheme.value === 'dark'
})

// 模态框样式
const modalStyle = computed(() => {
  if (isDark.value) {
    return {
      backgroundColor: '#1F2937',
      color: '#F9FAFB'
    }
  }
  return {
    backgroundColor: '#FFFFFF',
    color: '#1F2937'
  }
})

// Reactive data
const searchTerm = ref('')
const userInput = ref('')
const currentChat = ref(null)
const showPromptAssistanceModal = ref(false)
const showTermsBookModal = ref(false)
const sidebarCollapsed = ref(false)
const showConfigurationModal = ref(false)
const isUploadingDocument = ref(false) // Track document upload state
const pendingConversationId = ref(null) // Store conversation ID created for file upload
const uploadedFilesCount = ref(0) // Track number of files uploaded to pending conversation

// 段落交互Status
const showSourceModal = ref(false)
const currentSourceInfo = ref(null)
const currentQuotedText = ref('')
const messageParagraphsCache = new Map() // 缓存已解析的段落

// 学术词弹窗Status
const showAcademicTermsModal = ref(false)
const currentMessageForTerms = ref(null)

// Title editing state
const editingChatId = ref(null)
const editingChatTitle = ref('')

// Chat area resizable height
const chatAreaHeight = ref(500) // Default height in pixels
const isResizing = ref(false)
const minChatHeight = 200
const maxChatHeight = 700

// Chat history - initially empty
const chatHistory = ref([])

// Load chats from localStorage on mount
const loadChatsFromLocalStorage = () => {
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
  } catch (e) {
    console.error('Failed to load chat history:', e)
  }
}

// Save chats to localStorage
const saveChatsToLocalStorage = () => {
  try {
    storage.set('chat-history', chatHistory.value)
  } catch (e) {
    console.error('Failed to save chat history:', e)
  }
}

// Generate smart title using AI (based on AI response content)
const generateChatTitle = async (firstMessage, aiResponse) => {
  return await titleGenerator.generateTitle(firstMessage, aiResponse)
}

// Computed properties
const filteredChats = computed(() => {
  if (!searchTerm.value) return chatHistory.value
  return chatHistory.value.filter(chat => 
    chat.title.toLowerCase().includes(searchTerm.value.toLowerCase()) ||
    chat.messages.some(msg => msg.content.toLowerCase().includes(searchTerm.value.toLowerCase()))
  )
})

// Terms book count
const termsCount = computed(() => termsBookStore.currentTermsCount)

// Methods
const showConfiguration = () => {
  showConfigurationModal.value = true
}

const closeConfiguration = () => {
  showConfigurationModal.value = false
}

const newChat = async () => {
  // 1. Clear current chat and input
  currentChat.value = null
  userInput.value = ''

  // 2. Reset chat store state
  chatStore.instructionMode = false
  chatStore.messages = []
  chatStore.loading = false

  // 3. Clear any editing state
  editingChatId.value = null
  editingChatTitle.value = ''

  // 5. Close any open modals
  showPromptAssistanceModal.value = false
  showTermsBookModal.value = false

  // 6. Reset search
  searchTerm.value = ''

  // 7. Clear pending conversation state (for multi-file upload)
  pendingConversationId.value = null
  uploadedFilesCount.value = 0

  // 8. Initialize new session for terms book
  const newSessionId = Date.now().toString()
  termsBookStore.switchToNewSession(newSessionId)

  // 9. Note: We don't clear documents here anymore
  // Documents are now isolated by conversation_id
  // Each conversation has its own document context automatically

  // 10. Scroll chat area to top
  nextTick(() => {
    const chatContainer = document.getElementById('chat-container')
    if (chatContainer) {
      chatContainer.scrollTop = 0
    }
  })

  showNotification('New chat started with isolated document context')
}

const selectChat = (chat) => {
  currentChat.value = chat
  // Initialize terms book for this chat session
  termsBookStore.initSession(chat.id.toString())
  saveChatsToLocalStorage()
  showNotification(`Switched to: ${chat.title}`)
}

const deleteChat = (chat) => {
  const index = chatHistory.value.findIndex(c => c.id === chat.id)
  if (index > -1) {
    chatHistory.value.splice(index, 1)
    saveChatsToLocalStorage()
    showNotification('Chat deleted')
    if (currentChat.value?.id === chat.id) {
      currentChat.value = null
    }
  }
}

// Title editing methods
const startEditTitle = (chat) => {
  editingChatId.value = chat.id
  editingChatTitle.value = chat.title
  // Focus input on next tick
  nextTick(() => {
    const input = document.querySelector('.chat-item input')
    if (input) {
      input.focus()
      input.select()
    }
  })
}

const cancelEditTitle = () => {
  editingChatId.value = null
  editingChatTitle.value = ''
}

const saveEditedTitle = async (chat) => {
  const newTitle = editingChatTitle.value.trim()

  // If title hasn't changed or is empty, cancel
  if (!newTitle || newTitle === chat.title) {
    cancelEditTitle()
    return
  }

  try {
    // Get token from secure storage first, then fallback to legacy
    let token = await secureStorage.getSecure('token')
    if (!token) {
      token = storage.get('token')
    }

    if (!token) {
      showNotification('Please login first', 'error')
      cancelEditTitle()
      return
    }

    // Update title via API
    const response = await fetch(API_URLS.updateConversation(chat.id), {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ title: newTitle })
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to update title')
    }

    // Update local chat history
    chat.title = newTitle
    showNotification('Title updated successfully')
  } catch (error) {
    console.error('Error updating title:', error)
    showNotification(error.message || 'Failed to update title', 'error')
  } finally {
    cancelEditTitle()
  }
}

const sendMessage = async () => {
  const message = userInput.value.trim()
  if (!message) return

  // Check if API is configured
  const savedConfig = storage.get('api-configuration')
  let hasApiKey = false
  if (savedConfig) {
    try {
      hasApiKey = !!(savedConfig.apiKey || savedConfig.openaiApiKey || savedConfig.anthropicApiKey || savedConfig.cohereApiKey)
    } catch (e) {
      console.error('Failed to parse config:', e)
    }
  }

  let isNewChat = false

  // Check if there's a pending conversation with uploaded files
  if (!currentChat.value && pendingConversationId.value) {
    // Activate the pending conversation (files already uploaded to it)
    const pendingChat = chatHistory.value.find(chat => chat.id === pendingConversationId.value)
    if (pendingChat) {
      currentChat.value = pendingChat
      isNewChat = true
      // Clear pending state
      pendingConversationId.value = null
      uploadedFilesCount.value = 0
    }
  }

  if (!currentChat.value) {
    // Create new chat with default title
    isNewChat = true
    const newChatObj = {
      id: Date.now(),
      title: '新Chat',
      messages: [],
      isGeneratingTitle: false
    }
    chatHistory.value.unshift(newChatObj)
    currentChat.value = newChatObj
  }

  // Add user message
  currentChat.value.messages.push({
    id: Date.now(),
    sender: 'user',
    content: message,
    timestamp: new Date()
  })

  // Clear input
  userInput.value = ''
  autoResize()

  // Save to localStorage
  saveChatsToLocalStorage()

  // Check if API is available
  if (!hasApiKey) {
    // No API configured - show unavailable message
    setTimeout(() => {
      currentChat.value.messages.push({
        id: Date.now() + 1,
        sender: 'ai',
        content: 'Currently unavailable. Please configure an API Key (OpenAI, Anthropic or Cohere) in Settings first.',
        timestamp: new Date(),
        isComplete: true  // Error消息也是DoneStatus
      })

      // Scroll to bottom
      nextTick(() => {
        const chatContainer = document.getElementById('chat-container')
        if (chatContainer) {
          chatContainer.scrollTop = chatContainer.scrollHeight
        }
      })

      saveChatsToLocalStorage()
    }, 500)
    return
  }

  // Call real backend API using chat store
  try {
    // Show loading indicator
    const loadingId = Date.now() + 1
    currentChat.value.messages.push({
      id: loadingId,
      sender: 'ai',
      content: 'Thinking...',
      timestamp: new Date(),
      isLoading: true,
      isComplete: false  // 标记消息未Done,不显示工具栏
    })

    // Scroll to bottom
    nextTick(() => {
      const chatContainer = document.getElementById('chat-container')
      if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight
      }
    })

    // CRITICAL: Set the conversation ID in chat store before sending message
    // This ensures the backend receives the correct conversation_id for RAG context
    if (!chatStore.currentConversation || chatStore.currentConversation.id !== currentChat.value.id) {
      chatStore.currentConversation = {
        id: currentChat.value.id,
        title: currentChat.value.title,
        messages: chatStore.messages
      }
    }

    // Call backend API through chat store
    await chatStore.sendMessage(message, false)

    // Get the latest AI response from chat store
    const latestMessages = chatStore.messages
    let aiResponse = ''
    if (latestMessages.length > 0) {
      const lastMessage = latestMessages[latestMessages.length - 1]
      if (lastMessage.role === 'assistant') {
        aiResponse = lastMessage.content
      }
    }

    // Update the loading message with AI response
    const loadingIndex = currentChat.value.messages.findIndex(m => m.id === loadingId)
    if (loadingIndex > -1) {
      if (aiResponse) {
        // Get the latest AI message from chat store (which has suggestedQuestions)
        const latestAiMessage = chatStore.messages[chatStore.messages.length - 1]

        // Update existing message instead of creating new one
        // CRITICAL: Include suggestedQuestions from chat store
        currentChat.value.messages[loadingIndex] = {
          id: loadingId,
          sender: 'ai',
          content: aiResponse,
          timestamp: new Date(),
          isComplete: true,  // 标记消息已Done,显示工具栏
          suggestedQuestions: latestAiMessage.suggestedQuestions || []  // Copy suggested questions from chat store
        }
      } else {
        // If no response, remove loading message
        currentChat.value.messages.splice(loadingIndex, 1)
      }
    }

    // Generate smart title for new chats
    if (isNewChat && aiResponse) {
      currentChat.value.isGeneratingTitle = true
      // Force UI update to show "新Chat"
      saveChatsToLocalStorage()

      const generatedTitle = await generateChatTitle(message, aiResponse)
      // generateChatTitle now always returns a title (fallback to message if needed)
      currentChat.value.title = generatedTitle
      currentChat.value.isGeneratingTitle = false

      // Save again with the generated title
      saveChatsToLocalStorage()
    } else {
      // Save to localStorage for existing chats
      saveChatsToLocalStorage()
    }

    // Scroll to bottom
    nextTick(() => {
      const chatContainer = document.getElementById('chat-container')
      if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight
      }
    })
  } catch (error) {
    // Remove loading message if exists
    const loadingIndex = currentChat.value.messages.findIndex(m => m.isLoading)
    if (loadingIndex > -1) {
      currentChat.value.messages.splice(loadingIndex, 1)
    }

    // Show error message
    currentChat.value.messages.push({
      id: Date.now() + 3,
      sender: 'ai',
      content: 'Sorry, an error occurred. Please make sure API Key is configured correctly and try again.',
      timestamp: new Date(),
      isComplete: true  // Error消息也是DoneStatus
    })

    // Scroll to bottom
    nextTick(() => {
      const chatContainer = document.getElementById('chat-container')
      if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight
      }
    })
  }
}

const getAIResponse = (message) => {
  // This is a placeholder - in production, this would call the backend API
  const responses = [
    "That's a great question! Let me explain in detail...",
    "Based on my understanding, this question involves several aspects...",
    "According to your question, I suggest considering the following solutions...",
    "This is an interesting question! Let me analyze it for you...",
    "From multiple perspectives, this question can be understood as..."
  ]

  return responses[Math.floor(Math.random() * responses.length)] + " " + message
}

const autoResize = (event) => {
  const textarea = event?.target || document.querySelector('textarea')
  if (textarea) {
    textarea.style.height = 'auto'
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px'
  }
}

// 新的文件Upload successful处理
const handleFileUploaded = (file) => {
  console.log('File uploaded successfully:', file.name)
  ElMessage.success(`文件 ${file.name} Upload successful!`)

  // 可以在这里Refresh文档列表或更新UI
  // 例如：fetchDocuments()
}

// 新的文件上传Error处理
const handleUploadError = (error) => {
  console.error('Upload error:', error)
  ElMessage.error(error)
}

// 保留旧的handleFileUpload用于向后兼容
const handleFileUpload = async (files) => {
  if (files.length === 0) return

  // Get token from secure storage first, then fallback to legacy
  let token = await secureStorage.getSecure('token')
  if (!token) {
    token = storage.get('token')
  }

  if (!token) {
    showNotification('Please login first', 'error')
    return
  }

  // CRITICAL: Create or get conversation ID for file uploads
  let conversationId = pendingConversationId.value

  if (!conversationId) {
    // First, create a backend conversation by sending an initialization message
    // This ensures the conversation exists in the database before uploading files
    try {
      const initResponse = await fetch(API_URLS.chatMessage(), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          content: '[File upload session initialized]',
          conversationId: null  // null means create new conversation
        })
      })

      if (initResponse.ok) {
        const initData = await initResponse.json()
        if (initData.success && initData.conversationId) {
          conversationId = initData.conversationId

          // Create a hidden conversation in local chat history
          const hiddenChatObj = {
            id: conversationId,
            title: 'New conversation',
            messages: [],
            isGeneratingTitle: false
          }
          // Add to history but DON'T set as currentChat (keeps welcome page visible)
          chatHistory.value.unshift(hiddenChatObj)
          saveChatsToLocalStorage()

          pendingConversationId.value = conversationId
          uploadedFilesCount.value = 0
        } else {
          throw new Error('Failed to create conversation')
        }
      } else {
        throw new Error('Failed to initialize conversation for file upload')
      }
    } catch (error) {
      console.error('Failed to initialize conversation:', error)
      showNotification('Failed to prepare for file upload. Please try again.', 'error')
      return
    }
  }

  // Upload all files in parallel for better performance
  let successCount = 0
  let failCount = 0

  // Set uploading state
  isUploadingDocument.value = true

  // Create upload promises for all files
  const uploadPromises = files.map(async (file) => {
    // Check if file is PDF
    if (!file.name.endsWith('.pdf')) {
      showNotification(`Skipped ${file.name}: Only PDF files are supported`, 'warning')
      return { success: false, file }
    }

    const uploadNotificationId = `upload-${file.name}`
    showNotification(`Uploading ${file.name}...`, 'info', uploadNotificationId)

    try {
      // Create FormData
      const formData = new FormData()
      formData.append('file', file)

      // Upload to backend with conversation_id
      const uploadUrl = API_URLS.uploadDocument(conversationId)

      const response = await fetch(uploadUrl, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      })

      const data = await response.json()

      if (response.ok) {
        showNotification(`${file.name} uploaded successfully!`, 'success', uploadNotificationId)
        uploadedFilesCount.value++
        return { success: true, file }
      } else {
        showNotification(`Upload failed: ${data.detail || 'Unknown error'}`, 'error', uploadNotificationId)
        return { success: false, file }
      }
    } catch (error) {
      console.error('Upload error:', error)
      showNotification(`Upload failed: ${error.message}`, 'error', uploadNotificationId)
      return { success: false, file }
    }
  })

  // Wait for all uploads to complete
  const results = await Promise.all(uploadPromises)

  // Count successes and failures
  successCount = results.filter(r => r.success).length
  failCount = results.filter(r => !r.success).length

  // Always reset uploading state
  isUploadingDocument.value = false

  // Show summary
  if (successCount > 0) {
    showNotification(`Successfully uploaded ${successCount} file(s). You can now ask questions!`, 'success')
  }
}

const handleFileDrop = (event) => {
  event.preventDefault()
  const file = event.dataTransfer.files[0]
  if (file) {
    handleFileUpload([file])
  }
}

const showPromptAssistance = () => {
  showPromptAssistanceModal.value = true
  if (userInput.value.trim()) {
    ElMessage.info('You can optimize your current input in Prompt Assistant')
  }
}

const closePromptAssistance = () => {
  showPromptAssistanceModal.value = false
}

const showTermsBook = () => {
  showTermsBookModal.value = true
}

// Resize functionality for chat area
const startResize = (event) => {
  isResizing.value = true
  document.addEventListener('mousemove', handleResize)
  document.addEventListener('mouseup', stopResize)
  event.preventDefault()
}

const handleResize = (event) => {
  if (!isResizing.value) return
  const chatContainer = document.getElementById('chat-container')
  if (chatContainer) {
    const rect = chatContainer.getBoundingClientRect()
    const newHeight = event.clientY - rect.top
    chatAreaHeight.value = Math.min(Math.max(newHeight, minChatHeight), maxChatHeight)
  }
}

const stopResize = () => {
  isResizing.value = false
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
}

const toggleTheme = () => {
  const newTheme = themeManager.toggleTheme()
  const isDark = newTheme === 'dark'

  // Update background color
  document.body.style.backgroundColor = isDark ? 'var(--background)' : ''

  showNotification(`${isDark ? 'Dark' : 'Light'} mode activated`)
}

const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
  if (sidebarCollapsed.value) {
    showNotification('Sidebar collapsed')
  } else {
    showNotification('Sidebar expanded')
  }
}

const handleLogout = () => {
  showNotification('Logging out...')

  // Logout without changing theme
  authStore.logout()
  router.push('/')
}

// Track active notifications
let activeNotifications = new Map()

const showNotification = (message, type = 'info', notificationId = null) => {
  // If there's an existing notification with this ID, update it
  if (notificationId && activeNotifications.has(notificationId)) {
    const existingNotification = activeNotifications.get(notificationId)
    existingNotification.element.textContent = message

    // Reset the auto-dismiss timer
    if (existingNotification.timeoutId) {
      clearTimeout(existingNotification.timeoutId)
    }

    const timeoutId = setTimeout(() => {
      existingNotification.element.classList.add('opacity-0', 'transition-opacity', 'duration-300')
      setTimeout(() => {
        existingNotification.element.remove()
        activeNotifications.delete(notificationId)
      }, 300)
    }, 2000)

    existingNotification.timeoutId = timeoutId
    return
  }

  // Create new notification
  const notification = document.createElement('div')
  notification.className = 'fixed bottom-3 right-3 bg-gray-800 text-white px-3 py-1.5 rounded-md shadow-lg animate-fade-in z-50 text-sm theme-transition'
  notification.textContent = message
  document.body.appendChild(notification)

  const timeoutId = setTimeout(() => {
    notification.classList.add('opacity-0', 'transition-opacity', 'duration-300')
    setTimeout(() => {
      notification.remove()
      if (notificationId) {
        activeNotifications.delete(notificationId)
      }
    }, 300)
  }, 2000)

  // Store notification if it has an ID
  if (notificationId) {
    activeNotifications.set(notificationId, {
      element: notification,
      timeoutId: timeoutId
    })
  }
}

// Configuration marked 选项
marked.setOptions({
  breaks: true, // 支持换行
  gfm: true, // 支持 GitHub Flavored Markdown
})

// 渲染 Markdown 为 HTML with XSS protection
const renderMarkdown = (content) => {
  if (!content) return ''

  // Parse markdown to HTML and sanitize
  const html = marked.parse(content)
  return sanitizeMarkdown(html)
}

const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

// ========================================
// 段落交互功能
// ========================================

/**
 * 获Cancel息的段落列表（带缓存）
 */
const getMessageParagraphs = (message) => {
  const cacheKey = `${message.id}-${message.content.length}`

  if (messageParagraphsCache.has(cacheKey)) {
    return messageParagraphsCache.get(cacheKey)
  }

  // 渲染markdown并解析段落
  const html = renderMarkdown(message.content)
  const paragraphs = parseHtmlToParagraphs(html, message.sources || null)

  // 缓存结果
  messageParagraphsCache.set(cacheKey, paragraphs)

  return paragraphs
}

/**
 * 显示来源Information
 */
const handleShowSource = ({ text, source }) => {
  currentQuotedText.value = text
  currentSourceInfo.value = source
  showSourceModal.value = true
}

/**
 * 解释段落
 */
const handleExplainParagraph = async (text) => {
  // 构造解释请求
  const explainPrompt = `请解释：${text}`

  // 填入输入框
  userInput.value = explainPrompt

  // 自动Send
  await nextTick()
  await sendMessage()
}

/**
 * Search段落
 */
const handleSearchParagraph = (text) => {
  // 获取用户Settings的Search引擎（默认Google）
  const searchEngine = storage.get('searchEngine') || 'google'

  let searchUrl
  if (searchEngine === 'baidu') {
    searchUrl = `https://www.baidu.com/s?wd=${encodeURIComponent(text)}`
  } else {
    searchUrl = `https://www.google.com/search?q=${encodeURIComponent(text)}`
  }

  // 在新标签页打开
  window.open(searchUrl, '_blank', 'noopener,noreferrer')
}

/**
 * 打开原始文档
 */
const handleOpenDocument = (sourceInfo) => {
  if (!sourceInfo || !sourceInfo.documentUrl) {
    showNotification('文档链接不可用', 'warning')
    return
  }

  // 在新标签页打开文档
  window.open(sourceInfo.documentUrl, '_blank', 'noopener,noreferrer')
}

// ========================================
// AI消息工具栏功能
// ========================================

/**
 * Copy消息Content
 */
const handleCopyMessage = async (message) => {
  try {
    await navigator.clipboard.writeText(message.content)
    showNotification('Copied to clipboard', 'success')
  } catch (error) {
    console.error('Failed to copy:', error)
    showNotification('Failed to copy', 'error')
  }
}

/**
 * 处理联想问题点击
 */
const handleQuestionClick = (question) => {
  userInput.value = question
  // 自动聚焦到输入框
  nextTick(() => {
    const inputElement = document.querySelector('textarea')
    if (inputElement) {
      inputElement.focus()
      inputElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  })
}

/**
 * 获取问题按钮样式
 */
const getQuestionButtonStyle = () => {
  return isDark.value
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

/**
 * Regenerate消息
 */
const handleRegenerateMessage = async (message) => {
  if (!currentChat.value) return

  // Find the user message that prompted this AI response
  const messageIndex = currentChat.value.messages.findIndex(m => m.id === message.id)
  if (messageIndex <= 0) return

  const userMessage = currentChat.value.messages[messageIndex - 1]
  if (userMessage.sender !== 'user') return

  try {
    // Show loading state
    message.content = 'Regenerating...'
    message.isLoading = true
    message.isComplete = false  // 隐藏工具栏

    // Set conversation in chat store
    if (!chatStore.currentConversation || chatStore.currentConversation.id !== currentChat.value.id) {
      chatStore.currentConversation = {
        id: currentChat.value.id,
        title: currentChat.value.title,
        messages: chatStore.messages
      }
    }

    // Regenerate response
    await chatStore.sendMessage(userMessage.content, false)

    // Get new response
    const latestMessages = chatStore.messages
    if (latestMessages.length > 0) {
      const lastMessage = latestMessages[latestMessages.length - 1]
      if (lastMessage.role === 'assistant') {
        message.content = lastMessage.content
        message.isLoading = false
        message.isComplete = true  // 显示工具栏
      }
    }

    saveChatsToLocalStorage()
    showNotification('Response regenerated', 'success')
  } catch (error) {
    console.error('Failed to regenerate:', error)
    message.content = 'Failed to regenerate response. Please try again.'
    message.isLoading = false
    message.isComplete = true  // Error消息也显示工具栏
    showNotification('Regeneration failed', 'error')
  }
}

/**
 * 提取Academic Terms
 */
const handleExtractTerms = async (message) => {
  try {
    // Store the message for the modal to extract terms from
    currentMessageForTerms.value = message

    // Open modal - it will automatically call the backend API to extract terms
    showAcademicTermsModal.value = true
  } catch (error) {
    console.error('Failed to extract terms:', error)
    showNotification('Failed to extract academic terms', 'error')
  }
}

// ========================================
// 监听主题变化
// ========================================
watch(() => themeManager.getCurrentTheme(), (newTheme) => {
  currentTheme.value = newTheme
})

// 监听主题变化事件
onMounted(() => {
  // Load chat history from localStorage
  loadChatsFromLocalStorage()

  // Initialize terms book with current chat or default session
  if (currentChat.value) {
    termsBookStore.initSession(currentChat.value.id.toString())
  } else {
    // Initialize with a default session ID
    termsBookStore.initSession('default-session')
  }

  window.addEventListener('themechange', (event) => {
    currentTheme.value = event.detail
  })
})

onMounted(() => {
  // 使用主题管理器初始化
  themeManager.initTheme()

  currentTheme.value = themeManager.getCurrentTheme()

  document.body.style.backgroundColor = 'var(--background)'

  window.addEventListener('themechange', (event) => {
    const theme = event.detail
    currentTheme.value = theme
    document.body.style.backgroundColor = theme === 'dark' ? 'var(--background)' : ''
  })
})

// Cleanup resize listeners on unmount
onUnmounted(() => {
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
})
</script>

<style scoped>
/* ============================================
   FULL-SIZE WORKSPACE LAYOUT (Slack/Discord style)
   ============================================ */

/* Workspace wrapper - fills entire viewport */
.workspace-wrapper {
  width: 100vw;
  height: 100vh;
  display: flex;
  overflow: hidden;
  background-color: #f9fafb;
}

.dark .workspace-wrapper {
  background-color: var(--background);
}

/* Workspace container - fills entire wrapper */
.workspace-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: row;
  background-color: #ffffff;
  overflow: hidden;
}

.dark .workspace-container {
  background-color: var(--surface);
}

/* Left Sidebar - Fixed width, full height */
.sidebar {
  width: 240px;
  min-width: 240px;
  height: 100%;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  transition: all 0.3s ease;
  overflow: hidden;
}

/* Sidebar collapsed state */
.sidebar-collapsed {
  width: 60px !important;
  min-width: 60px !important;
}

.sidebar-collapsed .sidebar-content,
.sidebar-collapsed .p-3:not(.sidebar-footer) {
  opacity: 0;
  pointer-events: none;
}

.sidebar-collapsed .sidebar-footer span {
  display: none;
}

/* Sidebar content - scrollable area */
.sidebar-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}

/* Sidebar footer - always at bottom */
.sidebar-footer {
  flex-shrink: 0;
}

/* Main Content Area */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: #f9fafb;
}

.dark .main-content {
  background-color: var(--background);
}

/* Chat Area - Fills available space, scrollable */
.chat-area {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  min-height: 0; /* Important for flex scroll */
}

/* Input Area - Fixed height, always at bottom */
.input-area {
  flex-shrink: 0;
}

.compact-dashboard {
  font-size: 0.875rem;
}

.compact-chat {
  padding: 0.75rem;
}

.compact-input {
  padding: 0.75rem;
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

.animate-fade-in:nth-child(1) { animation-delay: 0.1s; }
.animate-fade-in:nth-child(2) { animation-delay: 0.2s; }
.animate-fade-in:nth-child(3) { animation-delay: 0.3s; }

.chat-item {
  max-height: 2.5rem;
}

.dark .compact-dashboard {
  background: var(--background);
  color: var(--text-primary);
}

.dark #sidebar {
  background: var(--surface);
  border-color: var(--border-light);
  color: var(--text-primary);
}

.dark .compact-chat {
  background: var(--background);
  color: var(--text-primary);
}

.dark .compact-input {
  background: var(--surface);
  border-color: var(--border-light);
  color: var(--text-primary);
}

.dark .compact-dashboard,
.dark .compact-dashboard * {
  color: inherit;
}

.dark input,
.dark textarea,
.dark select {
  color: var(--text-primary);
  background-color: var(--surface-elevated);
}

.dark input::placeholder,
.dark textarea::placeholder {
  color: var(--text-tertiary);
}

textarea,
select {
  transition: all 0.3s ease-in-out;
}

.dark button {
  color: var(--text-primary) !important;
}

.dark button span {
  color: var(--text-primary) !important;
}

.dark button i {
  color: var(--text-primary) !important;
}

.dark button.text-gray-700 {
  color: var(--text-primary) !important;
}

.dark button.text-gray-700 span {
  color: var(--text-primary) !important;
}

.dark button.text-gray-700 i {
  color: var(--text-primary) !important;
}

.dark textarea {
  color: var(--text-primary) !important;
}

.dark input {
  color: var(--text-primary) !important;
}

.dark select {
  color: var(--text-primary) !important;
}

.dark .text-gray-500,
.dark .text-gray-600,
.dark .text-gray-400 {
  color: var(--text-secondary) !important;
}

.dark .text-gray-700 {
  color: var(--text-primary) !important;
}

.dark .text-gray-800 {
  color: var(--text-primary) !important;
}

.dark .text-gray-900 {
  color: var(--text-primary) !important;
}

.dark kbd {
  color: var(--text-primary) !important;
}

.dark option {
  color: var(--text-primary) !important;
  background-color: var(--surface) !important;
}

:deep(.dark .bg-white.dark\:bg-surface) {
  color: #F9FAFB !important;
}

:deep(.dark .bg-white.dark\:bg-surface h3),
:deep(.dark .bg-white.dark\:bg-surface h4),
:deep(.dark .bg-white.dark\:bg-surface h5) {
  color: #F9FAFB !important;
}

:deep(.dark .bg-white.dark\:bg-surface p),
:deep(.dark .bg-white.dark\:bg-surface span),
:deep(.dark .bg-white.dark\:bg-surface div) {
  color: inherit;
}

:deep(.dark .bg-white.dark\:bg-surface .text-gray-500),
:deep(.dark .bg-white.dark\:bg-surface .text-gray-600),
:deep(.dark .bg-white.dark\:bg-surface .text-gray-400),
:deep(.dark .bg-white.dark\:bg-surface .text-gray-700),
:deep(.dark .bg-white.dark\:bg-surface .text-gray-800),
:deep(.dark .bg-white.dark\:bg-surface .text-gray-900) {
  color: #F9FAFB !important;
}

:deep(.dark .bg-white.dark\:bg-surface button) {
  color: #F9FAFB !important;
}

:deep(.dark .bg-white.dark\:bg-surface button span),
:deep(.dark .bg-white.dark\:bg-surface button i) {
  color: #F9FAFB !important;
}

/* Markdown Content样式 */
.markdown-content {
  line-height: 1.7;
  font-size: 14px;
}

/* Title样式 */
.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6) {
  font-weight: 600;
  margin-top: 1.5em;
  margin-bottom: 0.75em;
  line-height: 1.3;
}

.markdown-content :deep(h3) {
  font-size: 1.1em;
  padding-bottom: 0.3em;
  border-bottom: 1px solid #e5e7eb;
}

.dark .markdown-content :deep(h3) {
  border-bottom-color: #4b5563;
}

/* 段落样式 */
.markdown-content :deep(p) {
  margin-top: 0;
  margin-bottom: 1em;
}

/* 列表样式 */
.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  margin-top: 0.5em;
  margin-bottom: 1em;
  padding-left: 1.5em;
}

.markdown-content :deep(li) {
  margin-top: 0.25em;
  margin-bottom: 0.25em;
}

.markdown-content :deep(ul) {
  list-style-type: disc;
}

.markdown-content :deep(ol) {
  list-style-type: decimal;
}

/* 强调样式 */
.markdown-content :deep(strong) {
  font-weight: 600;
  color: inherit;
}

.markdown-content :deep(em) {
  font-style: italic;
}

/* 代码样式 */
.markdown-content :deep(code) {
  background-color: #f3f4f6;
  padding: 0.15em 0.4em;
  border-radius: 3px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 0.9em;
}

.dark .markdown-content :deep(code) {
  background-color: #374151;
  color: #e5e7eb;
}

.markdown-content :deep(pre) {
  background-color: #f3f4f6;
  padding: 1em;
  border-radius: 6px;
  overflow-x: auto;
  margin-top: 0.75em;
  margin-bottom: 0.75em;
}

.dark .markdown-content :deep(pre) {
  background-color: #374151;
}

.markdown-content :deep(pre code) {
  background-color: transparent;
  padding: 0;
  border-radius: 0;
  font-size: 0.85em;
}

/* 引用样式 */
.markdown-content :deep(blockquote) {
  border-left: 4px solid #3b82f6;
  padding-left: 1em;
  margin-left: 0;
  margin-top: 0.75em;
  margin-bottom: 0.75em;
  color: #6b7280;
  font-style: italic;
}

.dark .markdown-content :deep(blockquote) {
  border-left-color: #60a5fa;
  color: #9ca3af;
}

/* 分隔线样式 */
.markdown-content :deep(hr) {
  border: none;
  border-top: 2px solid #e5e7eb;
  margin: 1.5em 0;
}

.dark .markdown-content :deep(hr) {
  border-top-color: #4b5563;
}

/* 链接样式 */
.markdown-content :deep(a) {
  color: #3b82f6;
  text-decoration: underline;
}

.dark .markdown-content :deep(a) {
  color: #60a5fa;
}

.markdown-content :deep(a:hover) {
  color: #2563eb;
}

.dark .markdown-content :deep(a:hover) {
  color: #93c5fd;
}

/* 表格样式 */
.markdown-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin-top: 0.75em;
  margin-bottom: 0.75em;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  border: 1px solid #e5e7eb;
  padding: 0.5em 0.75em;
  text-align: left;
}

.dark .markdown-content :deep(th),
.dark .markdown-content :deep(td) {
  border-color: #4b5563;
}

.markdown-content :deep(th) {
  background-color: #f3f4f6;
  font-weight: 600;
}

.dark .markdown-content :deep(th) {
  background-color: #374151;
}

/* ========================================
   Suggested Questions Styling
   ======================================== */
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
