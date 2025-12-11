<template>
  <div class="chat-interface">
    <!-- 模式选择器 -->
    <div class="mode-selector">
      <el-radio-group v-model="currentMode" size="large">
        <el-radio-button value="chat">
          <el-icon><ChatDotRound /></el-icon>
          普通Chat
        </el-radio-button>
        <el-radio-button value="instruction">
          <el-icon><Tools /></el-icon>
          指令协助
        </el-radio-button>
      </el-radio-group>
    </div>

    <!-- 指令协助模式 -->
    <div v-if="currentMode === 'instruction'" class="instruction-assistant">
      <InstructionAssistant 
        @instruction-enhanced="handleEnhancedInstruction"
        @use-instruction="useEnhancedInstruction"
      />
    </div>

    <!-- 优化后的指令显示 -->
    <div v-if="chatStore.enhancedInstruction" class="enhanced-instruction">
      <el-alert
        :title="chatStore.enhancedInstruction"
        type="info"
        :closable="false"
        show-icon
      >
        <template #action>
          <el-button size="small" type="primary" @click="useEnhancedInstruction(chatStore.enhancedInstruction)">
            使用此指令
          </el-button>
          <el-button size="small" @click="chatStore.enhancedInstruction = ''">
            忽略
          </el-button>
        </template>
      </el-alert>
    </div>

    <!-- Chat消息区域 -->
    <div class="chat-messages" ref="messagesContainer">
      <!-- Welcome消息 -->
      <div v-if="chatStore.messages.length === 0" class="welcome-message">
        <div class="welcome-content">
          <div class="welcome-icon">🤖</div>
          <h2>Welcome使用 RAG智能助手</h2>
          <p>我可以帮您：</p>
          <div class="capabilities">
            <div class="capability">
              <el-icon><Search /></el-icon>
              <span>基于文档的智能问答</span>
            </div>
            <div class="capability">
              <el-icon><Document /></el-icon>
              <span>PDF文档Content分析</span>
            </div>
            <div class="capability">
              <el-icon><Tools /></el-icon>
              <span>指令优化和增强</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 消息列表 -->
      <div
        v-for="(message, index) in chatStore.messages"
        :key="index"
        :class="['message', message.role, { 'error-message': message.isError }]"
      >
        <div class="message-avatar">
          <el-avatar :size="40" :class="message.role">
            <span v-if="message.role === 'user'">👤</span>
            <span v-else-if="message.isError">⚠️</span>
            <span v-else>🤖</span>
          </el-avatar>
        </div>
        <div class="message-content">
          <div class="message-bubble" :class="{ 'error-bubble': message.isError }">
            <div class="message-text" v-html="formatMessage(message.content)"></div>
            <div class="message-actions" v-if="message.role === 'assistant'">
              <el-button
                size="small"
                text
                :icon="CopyDocument"
                @click="copyToClipboard(message.content)"
                title="Copy"
              />
            </div>
          </div>
          <!-- 联想Chat问题 -->
          <div
            v-if="message.role === 'assistant' && message.suggestedQuestions && message.suggestedQuestions.length > 0"
            class="suggested-questions"
          >
            <button
              v-for="(question, qIndex) in message.suggestedQuestions"
              :key="qIndex"
              class="suggested-question-btn"
              @click="handleQuestionClick(question)"
            >
              {{ question }}
            </button>
          </div>
          <div class="message-time">
            {{ formatTime(message.timestamp) }}
          </div>
        </div>
      </div>

      <!-- 加载Status -->
      <div v-if="chatStore.loading" class="loading-message">
        <div class="message-avatar">
          <el-avatar size="40" class="assistant">
            <span>🤖</span>
          </el-avatar>
        </div>
        <div class="message-content">
          <div class="message-bubble">
            <div class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Chat输入区域 -->
    <div class="chat-input-container">
      <!-- 快捷Actions -->
      <div class="quick-actions">
        <el-button
          v-for="action in quickActions"
          :key="action.text"
          :type="action.type"
          :icon="action.icon"
          size="small"
          @click="handleQuickAction(action)"
          class="quick-action-btn"
        >
          {{ action.text }}
        </el-button>
      </div>

      <!-- 输入框 -->
      <div class="input-wrapper">
        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="3"
          :placeholder="getPlaceholder()"
          resize="none"
          @keydown="handleKeydown"
          class="chat-input"
          maxlength="2000"
          show-word-limit
        />
        <div class="input-actions">
          <el-tooltip content="Upload Document" placement="top">
            <el-button :icon="Upload" @click="handleFileUpload" />
          </el-tooltip>
          <el-tooltip content="Send Message" placement="top">
            <el-button
              type="primary"
              :icon="Promotion"
              @click="sendMessage"
              :disabled="!inputMessage.trim() || chatStore.loading"
              :loading="chatStore.loading"
            />
          </el-tooltip>
        </div>
      </div>

      <!-- 功能Tips -->
      <div class="feature-hints">
        <span class="hint">
          <el-icon><Key /></el-icon>
          按 Enter Send，Shift + Enter 换行
        </span>
      </div>
    </div>

    <!-- 文件上传Chat框 -->
    <el-dialog
      v-model="showUploadDialog"
      title="Upload Document"
      width="500px"
    >
      <el-upload
        class="upload-demo"
        drag
        multiple
        accept=".pdf,.txt,.doc,.docx"
        :before-upload="beforeUpload"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        action="/api/upload"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 PDF、TXT、DOC、DOCX 格式文件，单个文件不超过 50MB
          </div>
        </template>
      </el-upload>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch } from 'vue'
import { useChatStore } from '@/stores/chat'
import { ElMessage } from 'element-plus'
import {
  ChatDotRound,
  Tools,
  Promotion,
  Upload,
  CopyDocument,
  Star,
  Search,
  Document,
  Key,
  UploadFilled
} from '@element-plus/icons-vue'

// 组件Import
import InstructionAssistant from './InstructionAssistant.vue'

const chatStore = useChatStore()
const inputMessage = ref('')
const messagesContainer = ref(null)
const showUploadDialog = ref(false)

// 当前模式
const currentMode = computed({
  get: () => chatStore.instructionMode ? 'instruction' : 'chat',
  set: (value) => {
    chatStore.instructionMode = value === 'instruction'
    if (value === 'chat') {
      chatStore.enhancedInstruction = ''
    }
  }
})

// 快捷Actions
const quickActions = [
  { 
    text: '总结Content', 
    icon: Search,
    type: 'primary',
    prompt: '请总结一下我们刚才讨论的主要Content'
  },
  { 
    text: '解释概念', 
    icon: Document,
    type: 'success',
    prompt: '请详细解释一下这个概念'
  },
  { 
    text: '提供建议', 
    icon: Tools,
    type: 'warning',
    prompt: '基于当前Content，你有什么建议？'
  },
  { 
    text: '举例说明', 
    icon: Star,
    type: 'info',
    prompt: '能否举一些具体的例子来说明？'
  }
]

// 获取输入框占位符
const getPlaceholder = () => {
  if (currentMode.value === 'instruction') {
    return '输入您的指令，AI会帮您优化为详细需求...'
  }
  return '输入您的问题，按 Enter Send...'
}

// 处理快捷键
const handleKeydown = (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

// Send Message
const sendMessage = async () => {
  if (!inputMessage.value.trim() || chatStore.loading) return

  const content = inputMessage.value.trim()
  const isInstruction = currentMode.value === 'instruction'
  
  await chatStore.sendMessage(content, isInstruction)
  inputMessage.value = ''
  
  // 滚动到底部
  nextTick(() => {
    scrollToBottom()
  })
  
  // 如果是指令模式，Send后自动切换回普通模式
  if (isInstruction) {
    currentMode.value = 'chat'
  }
}

// 处理快捷Actions
const handleQuickAction = (action) => {
  inputMessage.value = action.prompt
}

// 处理联想问题点击
const handleQuestionClick = (question) => {
  inputMessage.value = question
  // 自动滚动到输入框
  nextTick(() => {
    const inputWrapper = document.querySelector('.input-wrapper')
    if (inputWrapper) {
      inputWrapper.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  })
}

// 处理优化后的指令
const handleEnhancedInstruction = (enhancedInstruction) => {
  chatStore.enhancedInstruction = enhancedInstruction
}

// 使用优化后的指令
const useEnhancedInstruction = (instruction) => {
  inputMessage.value = instruction
  chatStore.enhancedInstruction = ''
  currentMode.value = 'chat'
  ElMessage.success('已Apply优化后的指令')
}

// Copy到剪贴板
const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已Copy到剪贴板')
  } catch (err) {
    console.error('CopyFailed:', err)
    ElMessage.error('CopyFailed')
  }
}

// 格式化消息Content
const formatMessage = (content) => {
  // 简单的Markdown样式转换
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br>')
}

// 格式化时间
const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 滚动到底部
const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 文件上传处理
const handleFileUpload = () => {
  showUploadDialog.value = true
}

const beforeUpload = (file) => {
  const isValidType = ['application/pdf', 'text/plain', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'].includes(file.type)
  const isValidSize = file.size / 1024 / 1024 < 50

  if (!isValidType) {
    ElMessage.error('只能上传 PDF、TXT、DOC、DOCX 格式的文件!')
    return false
  }
  if (!isValidSize) {
    ElMessage.error('File Size不能超过 50MB!')
    return false
  }
  return true
}

const handleUploadSuccess = (response) => {
  ElMessage.success('文件Upload successful')
  showUploadDialog.value = false
  // 这里可以触发文档处理逻辑
}

const handleUploadError = (error) => {
  ElMessage.error('文件Upload failed')
  console.error('Upload error:', error)
}

// 监听消息变化，自动滚动
watch(() => chatStore.messages.length, () => {
  nextTick(() => {
    scrollToBottom()
  })
})

// 监听加载Status变化
watch(() => chatStore.loading, (loading) => {
  if (!loading) {
    nextTick(() => {
      scrollToBottom()
    })
  }
})
</script>

<style scoped>
.chat-interface {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 12px;
  overflow: hidden;
}

.mode-selector {
  padding: 20px 20px 0;
  border-bottom: 1px solid #f0f0f0;
}

.instruction-assistant {
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
}

.enhanced-instruction {
  padding: 15px 20px;
  border-bottom: 1px solid #f0f0f0;
  background: #f8f9fa;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #f8f9fa;
}

.welcome-message {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  text-align: center;
}

.welcome-content {
  max-width: 500px;
}

.welcome-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.welcome-content h2 {
  margin: 0 0 16px 0;
  color: #333;
  font-size: 24px;
}

.welcome-content p {
  margin: 0 0 20px 0;
  color: #666;
  font-size: 16px;
}

.capabilities {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.capability {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: white;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  color: #333;
  font-size: 14px;
}

.message {
  display: flex;
  margin-bottom: 24px;
  animation: fadeIn 0.3s ease;
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  margin: 0 12px;
}

.message-avatar .el-avatar.user {
  background: #409eff;
}

.message-avatar .el-avatar.assistant {
  background: #67c23a;
}

.message-content {
  max-width: 70%;
  min-width: 200px;
}

.message.user .message-content {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.message-bubble {
  background: white;
  padding: 12px 16px;
  border-radius: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  position: relative;
}

.message.user .message-bubble {
  background: #409eff;
  color: white;
}

.error-bubble {
  background: #fef0f0 !important;
  border: 1px solid #f56c6c;
  color: #f56c6c;
}

.error-message .message-avatar .el-avatar {
  background: #f56c6c !important;
}

.message-text {
  line-height: 1.6;
  word-wrap: break-word;
}

.message-text :deep(strong) {
  font-weight: 600;
}

.message-text :deep(em) {
  font-style: italic;
}

.message-text :deep(code) {
  background: rgba(0, 0, 0, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
}

.message.user .message-text :deep(code) {
  background: rgba(255, 255, 255, 0.2);
}

.message-actions {
  display: flex;
  gap: 4px;
  margin-top: 8px;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.message-bubble:hover .message-actions {
  opacity: 1;
}

.message-time {
  font-size: 12px;
  color: #999;
  margin-top: 6px;
}

/* 联想Chat问题样式 */
.suggested-questions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 16px;
  width: 100%;
}

.suggested-question-btn {
  background: #ffffff;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 14px;
  color: #333;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: normal;
  word-wrap: break-word;
  line-height: 1.5;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.suggested-question-btn:hover {
  background: #f5f7fa;
  border-color: #409eff;
  color: #409eff;
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(64, 158, 255, 0.2);
}

.suggested-question-btn:active {
  transform: translateY(0);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.loading-message {
  display: flex;
  margin-bottom: 24px;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 8px 0;
}

.typing-indicator span {
  height: 8px;
  width: 8px;
  border-radius: 50%;
  background: #c1c1c1;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes typing {
  0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}

.chat-input-container {
  border-top: 1px solid #e4e7ed;
  padding: 20px;
  background: white;
}

.quick-actions {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.quick-action-btn {
  border-radius: 16px;
}

.input-wrapper {
  position: relative;
  margin-bottom: 12px;
}

.chat-input {
  width: 100%;
}

.chat-input :deep(.el-textarea__inner) {
  border-radius: 12px;
  padding-right: 100px;
  font-family: inherit;
  line-height: 1.5;
}

.input-actions {
  position: absolute;
  right: 8px;
  bottom: 8px;
  display: flex;
  gap: 4px;
}

.feature-hints {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #999;
}

.hint {
  display: flex;
  align-items: center;
  gap: 4px;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 滚动条样式 */
.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .message-content {
    max-width: 85%;
  }
  
  .capabilities {
    grid-template-columns: 1fr;
  }
  
  .feature-hints {
    flex-direction: column;
    gap: 4px;
  }
  
  .quick-actions {
    justify-content: center;
  }
}
</style>