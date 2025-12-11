import { defineStore } from 'pinia'

/**
 * 术语词本Store
 * 管理每个Chat的术语收藏
 */
export const useTermsBookStore = defineStore('termsBook', {
  state: () => ({
    // 当前会话ID
    currentSessionId: null,

    // 存储结构: { sessionId: [{ term, explanation }] }
    collections: {},

    // 是否已加载
    loaded: false
  }),

  getters: {
    /**
     * 获取当前会话的术语列表
     */
    currentTerms: (state) => {
      if (!state.currentSessionId) return []
      return state.collections[state.currentSessionId] || []
    },

    /**
     * 获取当前会话的术语Count
     */
    currentTermsCount: (state) => {
      if (!state.currentSessionId) return 0
      const terms = state.collections[state.currentSessionId] || []
      return terms.length
    },

    /**
     * 检查某个术语是否已收藏
     */
    isTermCollected: (state) => (term) => {
      if (!state.currentSessionId) return false
      const terms = state.collections[state.currentSessionId] || []
      return terms.some(t => t.term === term)
    }
  },

  actions: {
    /**
     * 初始化当前会话
     */
    initSession(sessionId) {
      this.currentSessionId = sessionId

      // 如果该会话没有术语集合，初始化空数组
      if (!this.collections[sessionId]) {
        this.collections[sessionId] = []
      }

      // 首次加载时从localStorage读取
      if (!this.loaded) {
        this.loadFromStorage()
        this.loaded = true
      }
    },

    /**
     * Add Term到当前会话
     */
    addTerm(term, explanation) {
      if (!this.currentSessionId) {
        console.error('No active session')
        return false
      }

      // 检查是否已存在（去重）
      if (this.isTermCollected(term)) {
        return false
      }

      // 添加到当前会话
      if (!this.collections[this.currentSessionId]) {
        this.collections[this.currentSessionId] = []
      }

      this.collections[this.currentSessionId].push({
        term,
        explanation,
        addedAt: new Date().toISOString()
      })

      // Save到localStorage
      this.saveToStorage()
      return true
    },

    /**
     * 批量Add Term
     */
    addTerms(termsList) {
      if (!this.currentSessionId) {
        console.error('No active session')
        return 0
      }

      let addedCount = 0
      termsList.forEach(({ term, explanation }) => {
        if (this.addTerm(term, explanation)) {
          addedCount++
        }
      })

      return addedCount
    },

    /**
     * 从当前会话移除术语
     */
    removeTerm(term) {
      if (!this.currentSessionId) return false

      const terms = this.collections[this.currentSessionId]
      if (!terms) return false

      const index = terms.findIndex(t => t.term === term)
      if (index !== -1) {
        terms.splice(index, 1)
        this.saveToStorage()
        return true
      }

      return false
    },

    /**
     * Clear当前会话的所有术语
     */
    clearCurrentSession() {
      if (!this.currentSessionId) return

      this.collections[this.currentSessionId] = []
      this.saveToStorage()
    },

    /**
     * Clear所有会话的术语
     */
    clearAll() {
      this.collections = {}
      this.saveToStorage()
    },

    /**
     * 切换到新会话（自动Clear）
     */
    switchToNewSession(sessionId) {
      this.currentSessionId = sessionId
      this.collections[sessionId] = []
      this.saveToStorage()
    },

    /**
     * Export当前会话的术语为Excel格式数据
     */
    exportCurrentTerms() {
      const terms = this.currentTerms
      if (terms.length === 0) return null

      // 返回二维数组格式，用于ExcelExport
      return [
        ['术语名称', 'Term Explanation'], // 表头
        ...terms.map(t => [t.term, t.explanation])
      ]
    },

    /**
     * Save到localStorage
     */
    saveToStorage() {
      try {
        const data = {
          currentSessionId: this.currentSessionId,
          collections: this.collections
        }
        localStorage.setItem('termsBook', JSON.stringify(data))
      } catch (error) {
        console.error('Failed to save terms book:', error)
      }
    },

    /**
     * 从localStorage加载
     */
    loadFromStorage() {
      try {
        const stored = localStorage.getItem('termsBook')
        if (stored) {
          const data = JSON.parse(stored)
          this.collections = data.collections || {}
          // 不恢复currentSessionId，由外部调用initSessionSettings
        }
      } catch (error) {
        console.error('Failed to load terms book:', error)
        this.collections = {}
      }
    }
  }
})
