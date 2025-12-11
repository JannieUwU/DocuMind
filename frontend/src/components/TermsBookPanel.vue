<template>
  <Transition name="panel-slide">
    <div v-if="isVisible" class="terms-book-panel" :style="panelStyle">
      <!-- 面板头部 -->
      <div class="panel-header" :style="headerStyle">
        <h3 class="panel-title">
          <i class="fa fa-book"></i>
          Terms Book
        </h3>
        <button
          class="close-btn"
          :style="closeBtnStyle"
          @click="handleClose"
        >
          <i class="fa fa-times"></i>
        </button>
      </div>

      <!-- 术语列表 -->
      <div class="terms-list" :style="listStyle">
        <!-- 空Status -->
        <div v-if="terms.length === 0" class="empty-state" :style="emptyStyle">
          <i class="fa fa-inbox empty-icon"></i>
          <p class="empty-text">No terms saved yet</p>
          <p class="empty-hint">Click "Add to Terms Book" in AI responses to save terms</p>
        </div>

        <!-- 术语项列表 -->
        <TransitionGroup v-else name="term-item" tag="div">
          <div
            v-for="(item, index) in terms"
            :key="item.term"
            class="term-item"
            :style="getItemStyle(index)"
          >
            <div class="term-content">
              <h4 class="term-name" :style="termNameStyle">{{ item.term }}</h4>
              <p class="term-explanation" :style="termExplanationStyle">
                {{ item.explanation }}
              </p>
            </div>
            <button
              class="delete-btn"
              :style="deleteBtnStyle"
              @click="handleRemoveTerm(item.term)"
              title="Remove"
            >
              <i class="fa fa-trash-o"></i>
            </button>
          </div>
        </TransitionGroup>
      </div>

      <!-- 底部Actions栏 -->
      <div class="panel-footer" :style="footerStyle">
        <div class="term-count" :style="countStyle">
          Total: {{ terms.length }} terms
        </div>
        <div class="action-buttons">
          <button
            class="action-btn export-btn"
            :style="exportBtnStyle"
            :disabled="terms.length === 0"
            @click="handleExport"
          >
            <i class="fa fa-file-excel-o"></i>
            <span>Export Excel</span>
          </button>
          <button
            class="action-btn clear-btn"
            :style="clearBtnStyle"
            :disabled="terms.length === 0"
            @click="handleClear"
          >
            <i class="fa fa-trash"></i>
            <span>Clear All</span>
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useTermsBookStore } from '@/stores/termsBook'
import * as XLSX from 'xlsx'

const props = defineProps({
  isVisible: {
    type: Boolean,
    required: true
  },
  isDark: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close'])

const termsBookStore = useTermsBookStore()

// 当前会话的术语列表
const terms = computed(() => termsBookStore.currentTerms)

// Close面板
const handleClose = () => {
  emit('close')
}

// 移除术语
const handleRemoveTerm = async (term) => {
  try {
    await ElMessageBox.confirm(
      `Are you sure you want to remove "${term}"?`,
      'Confirm Remove',
      {
        confirmButtonText: 'Remove',
        cancelButtonText: 'Cancel',
        type: 'warning'
      }
    )

    termsBookStore.removeTerm(term)
    ElMessage.success('Removed successfully')
  } catch (error) {
    // 用户Cancel
  }
}

// ExportExcel
const handleExport = () => {
  try {
    const data = termsBookStore.exportCurrentTerms()

    if (!data || data.length <= 1) {
      ElMessage.warning('No terms to export')
      return
    }

    // 创建工作簿
    const wb = XLSX.utils.book_new()

    // 创建工作表
    const ws = XLSX.utils.aoa_to_sheet(data)

    // Settings列宽
    ws['!cols'] = [
      { wch: 20 }, // 术语名称列
      { wch: 50 }  // Term Explanation列
    ]

    // 添加工作表到工作簿
    XLSX.utils.book_append_sheet(wb, ws, 'Terms Book')

    // 生成Filename
    const date = new Date().toISOString().split('T')[0]
    const filename = `terms-book_${date}.xlsx`

    // Export文件
    XLSX.writeFile(wb, filename)

    ElMessage.success('Exported successfully')
  } catch (error) {
    console.error('Export failed:', error)
    ElMessage.error('Export failed, please try again')
  }
}

// Clear词本
const handleClear = async () => {
  try {
    await ElMessageBox.confirm(
      'Are you sure you want to clear all terms in this conversation? This action cannot be undone.',
      'Confirm Clear',
      {
        confirmButtonText: 'Clear',
        cancelButtonText: 'Cancel',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )

    termsBookStore.clearCurrentSession()
    ElMessage.success('Cleared successfully')
  } catch (error) {
    // 用户Cancel
  }
}

// 样式计算
const panelStyle = computed(() => ({
  backgroundColor: props.isDark ? '#1F2937' : '#FFFFFF',
  borderColor: props.isDark ? '#374151' : '#E5E7EB',
  boxShadow: props.isDark
    ? '0 10px 25px rgba(0, 0, 0, 0.5)'
    : '0 10px 25px rgba(0, 0, 0, 0.15)'
}))

const headerStyle = computed(() => ({
  borderColor: props.isDark ? '#4B5563' : '#E5E7EB'
}))

const closeBtnStyle = computed(() => ({
  color: props.isDark ? '#9CA3AF' : '#6B7280'
}))

const listStyle = computed(() => ({
  backgroundColor: props.isDark ? 'rgba(17, 24, 39, 0.3)' : 'rgba(249, 250, 251, 0.5)'
}))

const emptyStyle = computed(() => ({
  color: props.isDark ? '#9CA3AF' : '#6B7280'
}))

const getItemStyle = (index) => ({
  backgroundColor: props.isDark ? '#374151' : '#FFFFFF',
  borderColor: props.isDark ? '#4B5563' : '#E5E7EB',
  animationDelay: `${index * 0.05}s`
})

const termNameStyle = computed(() => ({
  color: props.isDark ? '#60A5FA' : '#3B82F6'
}))

const termExplanationStyle = computed(() => ({
  color: props.isDark ? '#D1D5DB' : '#4B5563'
}))

const deleteBtnStyle = computed(() => ({
  color: props.isDark ? '#9CA3AF' : '#6B7280'
}))

const footerStyle = computed(() => ({
  borderColor: props.isDark ? '#4B5563' : '#E5E7EB',
  backgroundColor: props.isDark ? 'rgba(31, 41, 55, 0.8)' : 'rgba(249, 250, 251, 0.8)'
}))

const countStyle = computed(() => ({
  color: props.isDark ? '#9CA3AF' : '#6B7280'
}))

const exportBtnStyle = computed(() => ({
  backgroundColor: props.isDark ? '#1E40AF' : '#3B82F6',
  color: '#FFFFFF'
}))

const clearBtnStyle = computed(() => ({
  backgroundColor: props.isDark ? '#7F1D1D' : '#EF4444',
  color: '#FFFFFF'
}))
</script>

<style scoped>
.terms-book-panel {
  position: fixed;
  right: 0;
  top: 0;
  bottom: 0;
  width: 400px;
  border-left: 1px solid;
  display: flex;
  flex-direction: column;
  z-index: 999;
  transition: all 0.3s ease;
}

/* 面板头部 */
.panel-header {
  padding: 16px 20px;
  border-bottom: 1px solid;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

.panel-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.panel-title i {
  color: #3B82F6;
  font-size: 20px;
}

.close-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 6px;
  border-radius: 4px;
  font-size: 18px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(0, 0, 0, 0.05);
}

/* 术语列表 */
.terms-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

/* 空Status */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-text {
  font-size: 16px;
  font-weight: 500;
  margin: 0 0 8px 0;
}

.empty-hint {
  font-size: 13px;
  margin: 0;
  opacity: 0.7;
}

/* 术语项 */
.term-item {
  display: flex;
  gap: 12px;
  padding: 14px;
  border: 1px solid;
  border-radius: 8px;
  margin-bottom: 12px;
  transition: all 0.2s;
  animation: slideIn 0.3s ease forwards;
  opacity: 0;
}

.term-item:hover {
  transform: translateX(-4px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.term-content {
  flex: 1;
  min-width: 0;
}

.term-name {
  font-size: 15px;
  font-weight: 600;
  margin: 0 0 6px 0;
  word-wrap: break-word;
}

.term-explanation {
  font-size: 13px;
  line-height: 1.6;
  margin: 0;
  text-indent: 1em;
  word-wrap: break-word;
}

.delete-btn {
  flex-shrink: 0;
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 16px;
  transition: all 0.2s;
}

.delete-btn:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #EF4444;
  transform: scale(1.1);
}

/* 底部Actions栏 */
.panel-footer {
  padding: 16px 20px;
  border-top: 1px solid;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
  backdrop-filter: blur(8px);
}

.term-count {
  font-size: 13px;
  text-align: center;
}

.action-buttons {
  display: flex;
  gap: 12px;
}

.action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 16px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-btn:not(:disabled):hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.action-btn:not(:disabled):active {
  transform: translateY(0);
}

/* 动画 */
@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* 过渡动画 */
.panel-slide-enter-active {
  animation: panelSlideIn 0.3s ease;
}

.panel-slide-leave-active {
  animation: panelSlideOut 0.3s ease;
}

@keyframes panelSlideIn {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}

@keyframes panelSlideOut {
  from {
    transform: translateX(0);
  }
  to {
    transform: translateX(100%);
  }
}

.term-item-enter-active,
.term-item-leave-active {
  transition: all 0.3s ease;
}

.term-item-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.term-item-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

.term-item-move {
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
  .terms-book-panel {
    width: 100%;
    max-width: 400px;
  }
}

@media (max-width: 480px) {
  .terms-book-panel {
    width: 100vw;
    max-width: 100vw;
  }

  .panel-header {
    padding: 12px 16px;
  }

  .panel-title {
    font-size: 16px;
  }

  .terms-list {
    padding: 12px;
  }

  .term-item {
    padding: 12px;
  }

  .action-buttons {
    flex-direction: column;
  }

  .action-btn {
    width: 100%;
  }
}
</style>
