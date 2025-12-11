<template>
  <!-- Modal Overlay -->
  <Transition name="modal-fade">
    <div
      v-if="isVisible"
      class="modal-overlay"
      @click.self="handleClose"
    >
      <div
        class="modal-container"
        :style="modalStyle"
        @click.stop
      >
        <!-- Header -->
        <div class="modal-header" :style="headerStyle">
          <div class="header-content">
            <i class="fa fa-book header-icon"></i>
            <h2 class="header-title">Academic Terms Dictionary</h2>
            <span class="term-count" :style="countStyle">
              Total {{ filteredTerms.length }} terms
            </span>
          </div>
          <button
            class="close-btn"
            :style="closeButtonStyle"
            @click="handleClose"
          >
            <i class="fa fa-times"></i>
          </button>
        </div>

        <!-- Search Bar -->
        <div class="search-section" :style="searchStyle">
          <div class="search-input-wrapper">
            <i class="fa fa-search search-icon"></i>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search terms..."
              class="search-input"
              :style="inputStyle"
            />
            <button
              v-if="searchQuery"
              class="clear-btn"
              @click="searchQuery = ''"
              :style="clearBtnStyle"
            >
              <i class="fa fa-times-circle"></i>
            </button>
          </div>
        </div>

        <!-- Terms List -->
        <div class="terms-list" :style="listStyle">
          <div
            v-if="isExtracting"
            class="loading-state"
            :style="loadingStyle"
          >
            <i class="fa fa-spinner fa-spin loading-icon"></i>
            <p>Intelligently extracting academic terms...</p>
          </div>

          <div
            v-else-if="filteredTerms.length === 0 && !isExtracting"
            class="empty-state"
            :style="emptyStyle"
          >
            <i class="fa fa-inbox empty-icon"></i>
            <p>{{ searchQuery ? 'No matching terms found' : 'No terms yet' }}</p>
          </div>

          <TransitionGroup
            v-else
            name="term-list"
            tag="div"
            class="terms-container"
          >
            <div
              v-for="(term, index) in filteredTerms"
              :key="term.term"
              class="term-card"
              :style="getCardStyle(index)"
              @click="toggleExpand(term.term)"
            >
              <div class="term-header">
                <div class="term-title-row">
                  <h3 class="term-title" :style="termTitleStyle">
                    {{ term.term }}
                  </h3>
                  <button
                    class="favorite-btn"
                    :class="{ 'is-favorite': term.isFavorite }"
                    @click.stop="toggleFavorite(term.term)"
                    :style="favoriteButtonStyle(term.isFavorite)"
                  >
                    <i :class="term.isFavorite ? 'fa fa-star' : 'fa fa-star-o'"></i>
                  </button>
                </div>
                <p class="term-definition" :style="definitionStyle">
                  {{ term.definition }}
                </p>
              </div>

              <!-- Expanded Details -->
              <Transition name="expand">
                <div
                  v-if="expandedTerms.has(term.term)"
                  class="term-details"
                  :style="detailsStyle"
                >
                  <div v-if="term.example" class="detail-section">
                    <h4 class="detail-label" :style="labelStyle">
                      <i class="fa fa-lightbulb-o"></i> Example
                    </h4>
                    <p class="detail-content">{{ term.example }}</p>
                  </div>
                  <div v-if="term.context" class="detail-section">
                    <h4 class="detail-label" :style="labelStyle">
                      <i class="fa fa-file-text-o"></i> Context
                    </h4>
                    <p class="detail-content">{{ term.context }}</p>
                  </div>
                </div>
              </Transition>
            </div>
          </TransitionGroup>
        </div>

        <!-- Footer Actions -->
        <div class="modal-footer" :style="footerStyle">
          <button
            class="action-btn primary"
            :style="primaryBtnStyle"
            @click="addToTermsBook"
            :disabled="favoriteCount === 0"
          >
            <i class="fa fa-book"></i>
            <span>Add to Terms Book ({{ favoriteCount }})</span>
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useTermsBookStore } from '@/stores/termsBook'

const props = defineProps({
  isVisible: {
    type: Boolean,
    required: true
  },
  messageContent: {
    type: String,
    default: ''
  },
  isDark: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close'])

// Store
const termsBookStore = useTermsBookStore()

// State Management
const searchQuery = ref('')
const expandedTerms = ref(new Set())
const isExtracting = ref(false)
const terms = ref([])

// Favorite Term Count
const favoriteCount = computed(() => {
  return terms.value.filter(t => t.isFavorite).length
})

// Watch content changes and extract terms
watch(
  () => props.messageContent,
  (newContent) => {
    if (newContent && props.isVisible) {
      extractTerms(newContent)
    }
  },
  { immediate: true }
)

// Watch modal open status
watch(
  () => props.isVisible,
  (isVisible) => {
    if (isVisible && props.messageContent) {
      extractTerms(props.messageContent)
    }
  }
)

// Extract Academic Terms (call backend AI API)
const extractTerms = async (content) => {
  if (!content) return

  isExtracting.value = true

  try {
    // Call backend API for intelligent extraction - use unified API tool
    const { api } = await import('@/utils/api')

    console.log('[AcademicTerms] Sending request with content length:', content.length)

    const response = await api.post('/extract-terms', {
      content: content,
      use_ai: true  // Enable AI enhancement
    })

    console.log('[AcademicTerms] Received response:', response.data)

    const data = response.data

    if (data.success && data.terms && Array.isArray(data.terms)) {
      terms.value = data.terms
      console.log(`[AcademicTerms] Successfully extracted ${data.terms.length} terms`)

      if (data.terms.length === 0) {
        ElMessage.info('No academic terms found in content')
      } else {
        ElMessage.success(`Successfully extracted ${data.terms.length} academic terms`)
      }
    } else {
      throw new Error(data.message || 'Extraction failed')
    }

  } catch (error) {
    console.error('[AcademicTerms] Extraction failed:', error)

    // More detailed error information
    let errorMessage = 'Academic term extraction failed'
    if (error.response) {
      // API returned error
      errorMessage = error.response.data?.message || `API Error: ${error.response.status}`
    } else if (error.request) {
      // Request was sent but no response received
      errorMessage = 'Unable to connect to server, please check network connection'
    } else {
      // Other error
      errorMessage = error.message || 'Unknown error'
    }

    ElMessage.error(errorMessage)

    // Fallback: If API fails, use simple local extraction
    console.log('[AcademicTerms] Using fallback local extraction')
    terms.value = await extractTermsLocally(content)

    if (terms.value.length > 0) {
      ElMessage.info(`Found ${terms.value.length} possible terms using local extraction`)
    }
  } finally {
    isExtracting.value = false
  }
}

// Local simple extraction (fallback)
const extractTermsLocally = async (content) => {
  // Simple local extraction logic as backup
  const patterns = [
    /([A-Z][a-z]+(?:[A-Z][a-z]+)+)/g,  // CamelCase
    /([A-Z]{2,})/g,  // Acronyms
    /([\u4e00-\u9fa5]{2,6})(学习|网络|算法|模型|系统|架构)/g  // Chinese technical terms
  ]

  const found = new Set()

  for (const pattern of patterns) {
    const matches = content.match(pattern)
    if (matches) {
      matches.forEach(m => {
        if (m.length >= 2) found.add(m)
      })
    }
  }

  return Array.from(found).slice(0, 10).map(term => ({
    term: term,
    definition: `${term} is a professional term`,
    category: 'Professional Term',
    example: `In the technical field, ${term} has important applications`,
    context: '',
    isFavorite: false
  }))
}

// Filter terms
const filteredTerms = computed(() => {
  if (!searchQuery.value) return terms.value

  const query = searchQuery.value.toLowerCase()
  return terms.value.filter(
    term =>
      term.term.toLowerCase().includes(query) ||
      term.definition.toLowerCase().includes(query)
  )
})

// Toggle expand status
const toggleExpand = (termName) => {
  if (expandedTerms.value.has(termName)) {
    expandedTerms.value.delete(termName)
  } else {
    expandedTerms.value.add(termName)
  }
  // Trigger reactive update
  expandedTerms.value = new Set(expandedTerms.value)
}

// Toggle favorite status
const toggleFavorite = (termName) => {
  const term = terms.value.find(t => t.term === termName)
  if (term) {
    term.isFavorite = !term.isFavorite
  }
}

// Close modal
const handleClose = () => {
  searchQuery.value = ''
  expandedTerms.value.clear()
  emit('close')
}

// Add to terms book
const addToTermsBook = () => {
  const favoriteTerms = terms.value.filter(t => t.isFavorite)

  if (favoriteTerms.length === 0) {
    ElMessage.warning('Please mark terms to favorite first')
    return
  }

  // Batch add to terms book
  const addedCount = termsBookStore.addTerms(
    favoriteTerms.map(t => ({
      term: t.term,
      explanation: t.definition
    }))
  )

  if (addedCount > 0) {
    ElMessage.success(`Added ${addedCount} terms to terms book`)

    // Clear favorite marks for added terms
    favoriteTerms.forEach(t => {
      t.isFavorite = false
    })
  } else if (addedCount === 0 && favoriteTerms.length > 0) {
    ElMessage.info('Selected terms already in terms book')
  }
}

// Style calculations
const modalStyle = computed(() => ({
  backgroundColor: props.isDark ? '#1F2937' : '#FFFFFF',
  color: props.isDark ? '#F9FAFB' : '#1F2937',
  boxShadow: props.isDark
    ? '0 25px 50px -12px rgba(0, 0, 0, 0.5)'
    : '0 25px 50px -12px rgba(0, 0, 0, 0.25)'
}))

const headerStyle = computed(() => ({
  borderColor: props.isDark ? 'rgba(75, 85, 99, 0.5)' : 'rgba(229, 231, 235, 0.8)'
}))

const countStyle = computed(() => ({
  backgroundColor: props.isDark ? 'rgba(59, 130, 246, 0.2)' : 'rgba(59, 130, 246, 0.1)',
  color: props.isDark ? '#60A5FA' : '#3B82F6'
}))

const closeButtonStyle = computed(() => ({
  color: props.isDark ? '#9CA3AF' : '#6B7280'
}))

const searchStyle = computed(() => ({
  backgroundColor: props.isDark ? 'rgba(31, 41, 55, 0.5)' : 'rgba(249, 250, 251, 0.8)',
  borderColor: props.isDark ? 'rgba(75, 85, 99, 0.3)' : 'rgba(229, 231, 235, 0.5)'
}))

const inputStyle = computed(() => ({
  backgroundColor: props.isDark ? '#374151' : '#FFFFFF',
  color: props.isDark ? '#F9FAFB' : '#1F2937',
  borderColor: props.isDark ? '#4B5563' : '#E5E7EB'
}))

const clearBtnStyle = computed(() => ({
  color: props.isDark ? '#9CA3AF' : '#6B7280'
}))

const listStyle = computed(() => ({
  backgroundColor: props.isDark ? 'rgba(17, 24, 39, 0.3)' : 'rgba(249, 250, 251, 0.3)'
}))

const loadingStyle = computed(() => ({
  color: props.isDark ? '#9CA3AF' : '#6B7280'
}))

const emptyStyle = computed(() => ({
  color: props.isDark ? '#9CA3AF' : '#6B7280'
}))

const getCardStyle = (index) => ({
  backgroundColor: props.isDark ? '#374151' : '#FFFFFF',
  borderColor: props.isDark ? '#4B5563' : '#E5E7EB',
  animationDelay: `${index * 0.05}s`
})

const termTitleStyle = computed(() => ({
  color: props.isDark ? '#60A5FA' : '#3B82F6'
}))

const definitionStyle = computed(() => ({
  color: props.isDark ? '#D1D5DB' : '#4B5563'
}))

const favoriteButtonStyle = (isFavorite) => ({
  color: isFavorite
    ? '#FBBF24'
    : props.isDark ? '#6B7280' : '#9CA3AF'
})

const detailsStyle = computed(() => ({
  backgroundColor: props.isDark ? 'rgba(17, 24, 39, 0.5)' : 'rgba(249, 250, 251, 0.8)',
  borderColor: props.isDark ? 'rgba(75, 85, 99, 0.3)' : 'rgba(229, 231, 235, 0.5)',
  color: props.isDark ? '#E5E7EB' : '#374151'
}))

const labelStyle = computed(() => ({
  color: props.isDark ? '#9CA3AF' : '#6B7280'
}))

const footerStyle = computed(() => ({
  borderColor: props.isDark ? 'rgba(75, 85, 99, 0.5)' : 'rgba(229, 231, 235, 0.8)',
  backgroundColor: props.isDark ? 'rgba(31, 41, 55, 0.5)' : 'rgba(249, 250, 251, 0.5)'
}))

const primaryBtnStyle = computed(() => ({
  backgroundColor: '#3B82F6',
  color: '#FFFFFF'
}))
</script>

<style scoped>
/* Modal Overlay */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  padding: 20px;
}

/* Modal Container */
.modal-container {
  width: 100%;
  max-width: 700px;
  max-height: 85vh;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Header */
.modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-icon {
  font-size: 24px;
  color: #3B82F6;
}

.header-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.term-count {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(0, 0, 0, 0.05);
}

/* Search栏 */
.search-section {
  padding: 16px 24px;
  border-bottom: 1px solid;
  flex-shrink: 0;
}

.search-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 12px;
  color: #9CA3AF;
  font-size: 14px;
}

.search-input {
  width: 100%;
  padding: 10px 40px 10px 40px;
  border: 1px solid;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  transition: all 0.2s;
}

.search-input:focus {
  border-color: #3B82F6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.clear-btn {
  position: absolute;
  right: 8px;
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
}

.clear-btn:hover {
  background: rgba(0, 0, 0, 0.05);
}

/* 术语列表 */
.terms-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px;
  min-height: 300px;
}

.terms-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 加载和空Status */
.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.loading-icon,
.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.loading-icon {
  color: #3B82F6;
}

/* 术语卡片 */
.term-card {
  border: 1px solid;
  border-radius: 10px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  animation: slideIn 0.3s ease forwards;
  opacity: 0;
}

.term-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.term-header {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.term-title-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.term-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  flex: 1;
}

.favorite-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 18px;
  padding: 4px;
  transition: all 0.2s;
  border-radius: 4px;
}

.favorite-btn:hover {
  transform: scale(1.2);
}

.favorite-btn.is-favorite {
  animation: starPop 0.3s ease;
}

.term-definition {
  font-size: 14px;
  line-height: 1.6;
  margin: 0;
  text-indent: 1em;
}

/* 详细Content */
.term-details {
  margin-top: 12px;
  padding: 12px;
  border-radius: 6px;
  border: 1px solid;
}

.detail-section {
  margin-bottom: 12px;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.detail-label {
  font-size: 13px;
  font-weight: 600;
  margin: 0 0 6px 0;
  display: flex;
  align-items: center;
  gap: 6px;
}

.detail-content {
  font-size: 13px;
  line-height: 1.5;
  margin: 0;
  padding-left: 20px;
}

/* 底部Actions栏 */
.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid;
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-shrink: 0;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.action-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.action-btn:active:not(:disabled) {
  transform: translateY(0);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-btn.secondary {
  border: 1px solid;
}

.action-btn.primary {
  border: none;
}

/* 动画 */
@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes starPop {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.3);
  }
}

/* 过渡动画 */
.modal-fade-enter-active {
  transition: opacity 0.3s ease;
}

.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.modal-fade-enter-active .modal-container {
  animation: modalSlideIn 0.3s ease;
}

.modal-fade-leave-active .modal-container {
  animation: modalSlideOut 0.2s ease;
}

@keyframes modalSlideIn {
  from {
    transform: translateY(-30px) scale(0.95);
    opacity: 0;
  }
  to {
    transform: translateY(0) scale(1);
    opacity: 1;
  }
}

@keyframes modalSlideOut {
  from {
    transform: translateY(0) scale(1);
    opacity: 1;
  }
  to {
    transform: translateY(-20px) scale(0.95);
    opacity: 0;
  }
}

.expand-enter-active,
.expand-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
  margin-top: 0;
}

.expand-enter-to,
.expand-leave-from {
  opacity: 1;
  max-height: 500px;
  margin-top: 12px;
}

.term-list-enter-active,
.term-list-leave-active {
  transition: all 0.3s ease;
}

.term-list-enter-from {
  opacity: 0;
  transform: translateX(-30px);
}

.term-list-leave-to {
  opacity: 0;
  transform: translateX(30px);
}

.term-list-move {
  transition: transform 0.3s ease;
}

/* 滚动条样式 */
.terms-list::-webkit-scrollbar {
  width: 8px;
}

.terms-list::-webkit-scrollbar-track {
  background: transparent;
}

.terms-list::-webkit-scrollbar-thumb {
  background: rgba(156, 163, 175, 0.3);
  border-radius: 4px;
}

.terms-list::-webkit-scrollbar-thumb:hover {
  background: rgba(156, 163, 175, 0.5);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .modal-container {
    max-width: 100%;
    max-height: 90vh;
  }

  .modal-header {
    padding: 16px;
  }

  .header-title {
    font-size: 18px;
  }

  .search-section {
    padding: 12px 16px;
  }

  .terms-list {
    padding: 12px 16px;
  }

  .modal-footer {
    padding: 12px 16px;
    flex-direction: column;
  }

  .action-btn {
    width: 100%;
    justify-content: center;
  }
}
</style>
