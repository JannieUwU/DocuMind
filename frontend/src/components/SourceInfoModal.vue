<!--
  SourceInfoModal Component

  显示AI回复段落的来源文档Information
-->
<template>
  <Teleport to="body">
    <transition name="modal">
      <div v-if="visible" class="modal-overlay" @click="handleClose">
        <div class="modal-container" @click.stop>
          <!-- 模态框头部 -->
          <div class="modal-header">
            <h3 class="modal-title">
              <i class="fa fa-file-text-o mr-2"></i>
              来源Information
            </h3>
            <button @click="handleClose" class="close-btn">
              <i class="fa fa-times"></i>
            </button>
          </div>

          <!-- 模态框Content -->
          <div class="modal-body">
            <!-- 源文档Information -->
            <div class="source-info-section">
              <div class="info-item">
                <label class="info-label">
                  <i class="fa fa-file-pdf-o"></i>
                  文档名称
                </label>
                <div class="info-value">{{ sourceInfo?.documentName || '未知文档' }}</div>
              </div>

              <div class="info-item">
                <label class="info-label">
                  <i class="fa fa-bookmark-o"></i>
                  页码
                </label>
                <div class="info-value">第 {{ sourceInfo?.page || '?' }} 页</div>
              </div>

              <div class="info-item">
                <label class="info-label">
                  <i class="fa fa-map-marker"></i>
                  位置
                </label>
                <div class="info-value">{{ sourceInfo?.position || '未知位置' }}</div>
              </div>
            </div>

            <!-- 引用Content -->
            <div class="quote-section">
              <label class="section-label">
                <i class="fa fa-quote-left"></i>
                引用Content
              </label>
              <div class="quote-content">
                {{ quotedText }}
              </div>
            </div>

            <!-- 文档预览（可选） -->
            <div v-if="sourceInfo?.preview" class="preview-section">
              <label class="section-label">
                <i class="fa fa-eye"></i>
                文档预览
              </label>
              <div class="preview-content">
                {{ sourceInfo.preview }}
              </div>
            </div>

            <!-- 元数据 -->
            <div v-if="sourceInfo?.metadata" class="metadata-section">
              <label class="section-label">
                <i class="fa fa-info-circle"></i>
                其他Information
              </label>
              <div class="metadata-grid">
                <div
                  v-for="(value, key) in sourceInfo.metadata"
                  :key="key"
                  class="metadata-item"
                >
                  <span class="metadata-key">{{ formatKey(key) }}:</span>
                  <span class="metadata-value">{{ value }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 模态框底部 -->
          <div class="modal-footer">
            <button @click="openDocument" class="btn btn-primary">
              <i class="fa fa-external-link mr-1"></i>
              打开文档
            </button>
            <button @click="handleClose" class="btn btn-secondary">
              Close
            </button>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  sourceInfo: {
    type: Object,
    default: null
    // { documentName, page, position, preview, metadata, documentUrl }
  },
  quotedText: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['close', 'open-document'])

// Close模态框
const handleClose = () => {
  emit('close')
}

// 打开原始文档
const openDocument = () => {
  emit('open-document', props.sourceInfo)
}

// 格式化元数据键名
const formatKey = (key) => {
  return key
    .replace(/([A-Z])/g, ' $1')
    .replace(/^./, (str) => str.toUpperCase())
    .trim()
}
</script>

<style scoped>
/* 模态框遮罩 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
}

/* 模态框容器 */
.modal-container {
  background-color: #ffffff;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  max-width: 600px;
  width: 100%;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.dark .modal-container {
  background-color: #1f2937;
}

/* 模态框头部 */
.modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.dark .modal-header {
  border-bottom-color: #374151;
}

.modal-title {
  font-size: 18px;
  font-weight: 600;
  color: #111827;
  display: flex;
  align-items: center;
  margin: 0;
}

.dark .modal-title {
  color: #f9fafb;
}

.close-btn {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  border: none;
  background-color: transparent;
  color: #6b7280;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.close-btn:hover {
  background-color: #f3f4f6;
  color: #111827;
}

.dark .close-btn:hover {
  background-color: #374151;
  color: #f9fafb;
}

/* 模态框Content */
.modal-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

/* 来源Information部分 */
.source-info-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 24px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-label {
  font-size: 13px;
  font-weight: 600;
  color: #6b7280;
  display: flex;
  align-items: center;
  gap: 6px;
}

.dark .info-label {
  color: #9ca3af;
}

.info-value {
  font-size: 15px;
  color: #111827;
  padding: 10px 12px;
  background-color: #f9fafb;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.dark .info-value {
  color: #f9fafb;
  background-color: #374151;
  border-color: #4b5563;
}

/* 引用Content部分 */
.quote-section,
.preview-section {
  margin-bottom: 24px;
}

.section-label {
  font-size: 13px;
  font-weight: 600;
  color: #6b7280;
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 12px;
}

.dark .section-label {
  color: #9ca3af;
}

.quote-content {
  padding: 16px;
  background-color: #eff6ff;
  border-left: 4px solid #3b82f6;
  border-radius: 6px;
  color: #1e40af;
  font-style: italic;
  line-height: 1.6;
}

.dark .quote-content {
  background-color: rgba(59, 130, 246, 0.1);
  border-left-color: #60a5fa;
  color: #93c5fd;
}

.preview-content {
  padding: 16px;
  background-color: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  color: #374151;
  line-height: 1.6;
  max-height: 200px;
  overflow-y: auto;
}

.dark .preview-content {
  background-color: #374151;
  border-color: #4b5563;
  color: #d1d5db;
}

/* 元数据部分 */
.metadata-section {
  margin-bottom: 24px;
}

.metadata-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  padding: 16px;
  background-color: #f9fafb;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.dark .metadata-grid {
  background-color: #374151;
  border-color: #4b5563;
}

.metadata-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.metadata-key {
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
}

.dark .metadata-key {
  color: #9ca3af;
}

.metadata-value {
  font-size: 14px;
  color: #111827;
}

.dark .metadata-value {
  color: #f9fafb;
}

/* 模态框底部 */
.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.dark .modal-footer {
  border-top-color: #374151;
}

.btn {
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  display: flex;
  align-items: center;
  gap: 6px;
}

.btn-primary {
  background-color: #3b82f6;
  color: #ffffff;
}

.btn-primary:hover {
  background-color: #2563eb;
}

.btn-secondary {
  background-color: #f3f4f6;
  color: #374151;
}

.btn-secondary:hover {
  background-color: #e5e7eb;
}

.dark .btn-secondary {
  background-color: #374151;
  color: #f9fafb;
}

.dark .btn-secondary:hover {
  background-color: #4b5563;
}

/* 模态框动画 */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.9);
}

/* 实用类 */
.mr-1 {
  margin-right: 4px;
}

.mr-2 {
  margin-right: 8px;
}
</style>
