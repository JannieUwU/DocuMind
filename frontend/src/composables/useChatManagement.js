/**
 * Chat Management Composable
 *
 * Manages chat state and operations for the dashboard.
 * Optimized with computed properties and memoization.
 */

import { ref, computed } from 'vue'
import { useChatStore } from '@/stores/chat'
import titleGenerator from '@/services/titleGenerator.service'
import chatHistoryManager from '@/services/chatHistoryManager.service'
import { ErrorHandler } from '@/utils/errorHandler'

/**
 * @typedef {import('@/types/api.types').ChatConversation} ChatConversation
 * @typedef {import('@/types/api.types').ChatMessage} ChatMessage
 */

export function useChatManagement() {
  const chatStore = useChatStore()

  // Local state
  const currentChat = ref(null)
  const searchTerm = ref('')
  const editingChatId = ref(null)
  const editingChatTitle = ref('')

  /**
   * Filtered and sorted chats
   * Memoized to prevent unnecessary recalculations
   */
  const filteredChats = computed(() => {
    let chats = chatStore.conversations || []

    // Filter by search term
    if (searchTerm.value.trim()) {
      const term = searchTerm.value.toLowerCase().trim()
      chats = chats.filter(chat =>
        chat.title.toLowerCase().includes(term)
      )
    }

    // Sort by last message timestamp (most recent first)
    return chats.sort((a, b) => {
      const aTime = new Date(a.updated_at || a.created_at)
      const bTime = new Date(b.updated_at || b.created_at)
      return bTime - aTime
    })
  })

  /**
   * Current chat messages
   * Memoized and sorted by timestamp
   */
  const currentMessages = computed(() => {
    if (!currentChat.value || !currentChat.value.messages) {
      return []
    }

    return [...currentChat.value.messages].sort((a, b) => {
      const aTime = new Date(a.timestamp)
      const bTime = new Date(b.timestamp)
      return aTime - bTime
    })
  })

  /**
   * Check if current chat has messages
   */
  const hasMessages = computed(() => {
    return currentMessages.value.length > 0
  })

  /**
   * Get current chat ID
   */
  const currentChatId = computed(() => {
    return currentChat.value?.id || null
  })

  /**
   * Create a new chat
   */
  async function createNewChat() {
    try {
      const newChat = await chatStore.createConversation()
      currentChat.value = newChat
      return newChat
    } catch (error) {
      const appError = ErrorHandler.handleApiError(error)
      ErrorHandler.logError(appError, 'useChatManagement.createNewChat')
      throw appError
    }
  }

  /**
   * Select a chat
   * @param {ChatConversation} chat - Chat to select
   */
  function selectChat(chat) {
    currentChat.value = chat
  }

  /**
   * Delete a chat
   * @param {ChatConversation} chat - Chat to delete
   */
  async function deleteChat(chat) {
    try {
      await chatStore.deleteConversation(chat.id)

      // If deleted chat was current, clear selection
      if (currentChat.value?.id === chat.id) {
        currentChat.value = null
      }

      return true
    } catch (error) {
      const appError = ErrorHandler.handleApiError(error)
      ErrorHandler.logError(appError, 'useChatManagement.deleteChat')
      throw appError
    }
  }

  /**
   * Start editing chat title
   * @param {ChatConversation} chat - Chat to edit
   */
  function startEditTitle(chat) {
    editingChatId.value = chat.id
    editingChatTitle.value = chat.title
  }

  /**
   * Save edited title
   * @param {ChatConversation} chat - Chat being edited
   * @param {string} newTitle - New title
   */
  async function saveEditedTitle(chat, newTitle) {
    const trimmedTitle = newTitle.trim()

    if (!trimmedTitle || trimmedTitle === chat.title) {
      cancelEditTitle()
      return
    }

    try {
      await chatStore.updateConversation(chat.id, { title: trimmedTitle })
      chat.title = trimmedTitle
      cancelEditTitle()
    } catch (error) {
      const appError = ErrorHandler.handleApiError(error)
      ErrorHandler.logError(appError, 'useChatManagement.saveEditedTitle')
      throw appError
    }
  }

  /**
   * Cancel editing title
   */
  function cancelEditTitle() {
    editingChatId.value = null
    editingChatTitle.value = ''
  }

  /**
   * Generate title for chat
   * @param {ChatConversation} chat - Chat to generate title for
   * @param {string} userMessage - User's first message
   * @param {string} aiResponse - AI's response
   */
  async function generateChatTitle(chat, userMessage, aiResponse) {
    try {
      // Mark as generating
      chat.isGeneratingTitle = true

      const title = await titleGenerator.generateTitle(userMessage, aiResponse)

      // Update chat with generated title
      await chatStore.updateConversation(chat.id, { title })
      chat.title = title
      chat.isGeneratingTitle = false

      return title
    } catch (error) {
      chat.isGeneratingTitle = false
      ErrorHandler.logError(error, 'useChatManagement.generateChatTitle')
      // Return fallback title on error
      return `Chat ${new Date().toLocaleDateString()}`
    }
  }

  /**
   * Add message to current chat
   * @param {ChatMessage} message - Message to add
   */
  function addMessage(message) {
    if (currentChat.value) {
      if (!currentChat.value.messages) {
        currentChat.value.messages = []
      }
      currentChat.value.messages.push(message)
    }
  }

  /**
   * Update last message in current chat
   * @param {Partial<ChatMessage>} updates - Message updates
   */
  function updateLastMessage(updates) {
    if (currentChat.value && currentChat.value.messages?.length > 0) {
      const lastMessage = currentChat.value.messages[currentChat.value.messages.length - 1]
      Object.assign(lastMessage, updates)
    }
  }

  /**
   * Save conversation to history with automatic trimming
   * @param {ChatConversation} conversation - Conversation to save
   * @returns {boolean} Success status
   */
  function saveToHistory(conversation) {
    try {
      return chatHistoryManager.saveConversation(conversation)
    } catch (error) {
      ErrorHandler.logError(error, 'useChatManagement.saveToHistory')
      return false
    }
  }

  /**
   * Load conversations from history
   * @returns {ChatConversation[]} Loaded conversations
   */
  function loadFromHistory() {
    try {
      return chatHistoryManager.load()
    } catch (error) {
      ErrorHandler.logError(error, 'useChatManagement.loadFromHistory')
      return []
    }
  }

  /**
   * Save all conversations to history
   * @param {ChatConversation[]} conversations - All conversations
   * @returns {boolean} Success status
   */
  function saveAllToHistory(conversations) {
    try {
      return chatHistoryManager.save(conversations)
    } catch (error) {
      ErrorHandler.logError(error, 'useChatManagement.saveAllToHistory')
      return false
    }
  }

  /**
   * Delete conversation from history
   * @param {string | number} conversationId - ID of conversation to delete
   * @returns {boolean} Success status
   */
  function deleteFromHistory(conversationId) {
    try {
      return chatHistoryManager.deleteConversation(conversationId)
    } catch (error) {
      ErrorHandler.logError(error, 'useChatManagement.deleteFromHistory')
      return false
    }
  }

  return {
    // State
    currentChat,
    searchTerm,
    editingChatId,
    editingChatTitle,

    // Computed
    filteredChats,
    currentMessages,
    hasMessages,
    currentChatId,

    // Methods
    createNewChat,
    selectChat,
    deleteChat,
    startEditTitle,
    saveEditedTitle,
    cancelEditTitle,
    generateChatTitle,
    addMessage,
    updateLastMessage,

    // History management (with automatic trimming)
    saveToHistory,
    loadFromHistory,
    saveAllToHistory,
    deleteFromHistory
  }
}
