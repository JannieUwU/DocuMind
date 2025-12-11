import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/utils/api'
import requestCancellation, { REQUEST_TYPES } from '@/services/requestCancellation.service'

export const useChatStore = defineStore('chat', () => {
  // Chat History
  const conversations = ref([])
  const currentConversation = ref(null)
  const messages = ref([])
  
  // Search和Filter
  const searchTerm = ref('')

  // 模式Status
  const instructionMode = ref(false)
  const enhancedInstruction = ref('')
  
  // 加载Status
  const loading = ref(false)

  // Filter后的Chat列表
  const filteredConversations = computed(() => {
    if (!searchTerm.value) return conversations.value
    return conversations.value.filter(conv =>
      conv.title.toLowerCase().includes(searchTerm.value.toLowerCase())
    )
  })

  // 模拟Chat数据
  const mockConversations = [
    {
      id: 1,
      title: '关于人工智能的讨论',
      messages: [
        { role: 'user', content: '什么是人工智能？', timestamp: new Date().toISOString() },
        { role: 'assistant', content: '人工智能是计算机科学的一个分支，旨在创造能够执行通常需要人类智能的任务的机器。', timestamp: new Date().toISOString() }
      ],
      createdAt: new Date().toISOString()
    },
    {
      id: 2,
      title: '机器学习Apply场景',
      messages: [
        { role: 'user', content: '机器学习有哪些Apply场景？', timestamp: new Date().toISOString() },
        { role: 'assistant', content: '机器学习广泛Apply于推荐系统、图像识别、自然语言处理等领域。', timestamp: new Date().toISOString() }
      ],
      createdAt: new Date().toISOString()
    }
  ]

  // 获取Chat History
  const fetchConversations = async () => {
    loading.value = true
    try {
      const response = await api.get('/chat/conversations')
      if (response.data) {
        conversations.value = response.data
      }
    } catch (error) {
      console.error('获取Chat HistoryFailed:', error)
      // 如果后端不可用，使用模拟数据
      if (error.response?.status === 401) {
        conversations.value = mockConversations
      }
    } finally {
      loading.value = false
    }
  }

  // 确保后端Configuration已同步
  const ensureConfigSynced = async () => {
    const savedConfig = localStorage.getItem('api-configuration')
    if (savedConfig) {
      try {
        const configData = JSON.parse(savedConfig)
        // 只有当有 API key 时才同步
        if (configData.apiKey || configData.anthropicApiKey) {
          await api.post('/config', configData)
          return true
        }
      } catch (error) {
        console.error('同步Configuration failed:', error)
      }
    }
    return false
  }

  // Send Message
  const sendMessage = async (content, isInstruction = false) => {
    const message = {
      role: 'user',
      content,
      timestamp: new Date().toISOString()
    }

    messages.value.push(message)
    loading.value = true

    // Add a temporary incomplete AI message placeholder
    const tempMessageIndex = messages.value.length
    const tempMessage = {
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      isComplete: false  // Mark as incomplete during generation
    }
    messages.value.push(tempMessage)

    // Register cancellable request
    const conversationId = currentConversation.value?.id || 'new'
    const { id: requestId, signal } = requestCancellation.register(
      REQUEST_TYPES.CHAT_MESSAGE,
      conversationId
    )

    try {
      // 先确保后端Configuration已同步
      await ensureConfigSynced()

      // 调用后端 API with cancellation signal
      const response = await api.post('/chat/message', {
        content: content,
        conversationId: currentConversation.value?.id || null
      }, {
        signal  // Pass AbortSignal to axios
      })

      if (response.data && response.data.success) {
        // Update the temporary message with actual content
        messages.value[tempMessageIndex].content = response.data.response
        messages.value[tempMessageIndex].isComplete = true

        // Store suggested questions if available
        if (response.data.suggestedQuestions && Array.isArray(response.data.suggestedQuestions)) {
          messages.value[tempMessageIndex].suggestedQuestions = response.data.suggestedQuestions
        }

        // 更新当前Chat ID
        if (!currentConversation.value && response.data.conversationId) {
          const newConversation = {
            id: response.data.conversationId,
            title: content.substring(0, 20) + '...',
            messages: [...messages.value],
            createdAt: new Date().toISOString()
          }
          conversations.value.unshift(newConversation)
          currentConversation.value = newConversation
        }
      } else {
        throw new Error(response.data?.message || 'Unknown error')
      }

    } catch (error) {
      // Check if request was cancelled
      if (error.name === 'AbortError' || error.name === 'CanceledError') {
        console.log('Request cancelled:', requestId)
        // Remove the user message and temp AI message that were added
        messages.value.pop()  // Remove temp AI message
        messages.value.pop()  // Remove user message
        return { cancelled: true }
      }

      console.error('Send MessageFailed:', error)

      // 提供更详细的Error处理和用户Tips
      let errorContent = '抱歉，发生了Error。'

      if (error.response?.data?.detail) {
        errorContent = error.response.data.detail
      } else if (error.response?.status === 429) {
        errorContent = 'API 服务当前负载较高，请稍后重试。建议等待 1-2 分钟后再试。'
      } else if (error.response?.status === 401) {
        errorContent = '身份验证Failed，请重新Login。'
      } else if (error.response?.status === 500) {
        errorContent = 'Server error，请稍后重试。如果问题持续，请检查 API Configuration。'
      } else if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        errorContent = 'Request timeout，请检查网络连接后重试。'
      } else if (!navigator.onLine) {
        errorContent = '网络连接已断开，请检查您的网络Settings。'
      } else {
        errorContent = '抱歉，发生了Unknown error，请稍后重试。请确保已Login并Configuration了正确的 API Key。'
      }

      // Update the temp message with error content
      messages.value[tempMessageIndex].content = errorContent
      messages.value[tempMessageIndex].isError = true
      messages.value[tempMessageIndex].isComplete = true
    } finally {
      loading.value = false
      // Cleanup completed request
      requestCancellation.cleanup(requestId)
    }
  }

  // Optimize Instruction
  const enhanceInstruction = async (instruction) => {
    try {
      const response = await api.post('/instruction/enhance', {
        instruction: instruction
      })

      if (response.data && response.data.success) {
        const enhanced = response.data.enhancedInstruction
        enhancedInstruction.value = enhanced
        return { enhancedInstruction: enhanced }
      } else {
        throw new Error('优化Failed')
      }
    } catch (error) {
      console.error('Optimize InstructionFailed:', error)
      // 如果后端不可用，使用本地模拟
      const enhanced = `优化后的详细指令：请基于"${instruction}"提供全面的分析，包括背景介绍、关键要点、实际Apply场景以及相关建议。要求回答结构清晰、Content详实。`
      enhancedInstruction.value = enhanced
      return { enhancedInstruction: enhanced }
    }
  }

  // New Chat
  const newConversation = () => {
    // Cancel any pending requests for current conversation
    if (currentConversation.value) {
      requestCancellation.cancelByConversation(currentConversation.value.id)
    }

    currentConversation.value = null
    messages.value = []
    enhancedInstruction.value = ''
    instructionMode.value = false
  }

  // Cancel current message generation
  const cancelCurrentMessage = () => {
    const conversationId = currentConversation.value?.id || 'new'
    const cancelled = requestCancellation.cancelByConversation(
      conversationId,
      REQUEST_TYPES.CHAT_MESSAGE
    )

    if (cancelled > 0) {
      loading.value = false
      // Remove the last user message if it was just added
      if (messages.value.length > 0 && messages.value[messages.value.length - 1].role === 'user') {
        messages.value.pop()
      }
    }

    return cancelled > 0
  }

  // Switch conversation (cancel pending requests for old one)
  const switchConversation = (conversation) => {
    // Cancel pending requests for current conversation
    if (currentConversation.value) {
      requestCancellation.cancelByConversation(currentConversation.value.id)
    }

    currentConversation.value = conversation
    messages.value = conversation.messages || []
  }

  return {
    // Status
    conversations,
    currentConversation,
    messages,
    searchTerm,
    instructionMode,
    enhancedInstruction,
    loading,

    // 计算属性
    filteredConversations,

    // 方法
    fetchConversations,
    sendMessage,
    enhanceInstruction,
    newConversation,
    cancelCurrentMessage,
    switchConversation
  }
})