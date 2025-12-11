<template>
  <div class="conversation-history">
    <!-- Search框 -->
    <div class="search-section">
      <div class="relative">
        <input
          v-model="chatStore.searchTerm"
          type="text"
          placeholder="Search conversations..."
          class="search-input"
        />
        <span class="search-icon">
          <i class="fa fa-search"></i>
        </span>
      </div>
    </div>

    <!-- New Chat按钮 -->
    <div class="new-conversation-section">
      <button @click="handleNewConversation" class="new-conversation-btn">
        <i class="fa fa-plus"></i>
        <span>New Chat</span>
      </button>
    </div>

    <!-- Chat列表 -->
    <div class="conversation-list">
      <div class="section-header">
        <span>Chat History</span>
        <span class="count">({{ chatStore.filteredConversations.length }})</span>
      </div>

      <!-- 加载Status -->
      <div v-if="chatStore.loading" class="loading-section">
        <div class="skeleton-item"></div>
        <div class="skeleton-item"></div>
        <div class="skeleton-item"></div>
      </div>

      <!-- Chat列表 -->
      <div v-else-if="chatStore.filteredConversations.length > 0" class="conversations">
        <div
          v-for="conversation in chatStore.filteredConversations"
          :key="conversation.id"
          :class="['conversation-item', { active: isActive(conversation.id) }]"
          @click="handleSelectConversation(conversation)"
        >
          <div class="conversation-header">
            <div class="conversation-title">
              <i class="fa fa-comment-o"></i>
              <span class="title-text">{{ conversation.title }}</span>
            </div>
            <div class="conversation-actions">
              <button
                @click.stop="handleDeleteConversation(conversation)"
                class="delete-btn"
              >
                <i class="fa fa-trash-o"></i>
              </button>
            </div>
          </div>

          <div class="conversation-meta">
            <span class="time">{{ formatTime(conversation.createdAt) }}</span>
            <span class="message-count">{{ conversation.messages?.length || 0 }} messages</span>
          </div>
        </div>
      </div>

      <!-- 空Status -->
      <div v-else class="empty-state">
        <div class="empty-icon">
          <i class="fa fa-comments"></i>
        </div>
        <p class="empty-text">No conversations yet</p>
        <p class="empty-subtext">Start a new chat to begin!</p>
      </div>
    </div>

    <!-- 底部区域 -->
    <div class="sidebar-footer">
      <div class="footer-actions">
        <button class="footer-btn" @click="toggleTheme">
          <i class="fa" :class="themeIcon"></i>
          <span>{{ themeText }}</span>
        </button>
        <button class="footer-btn" @click="toggleSidebar">
          <i class="fa fa-chevron-left"></i>
          <span>Collapse</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useChatStore } from '@/stores/chat'
import { ElMessage, ElMessageBox } from 'element-plus'

const chatStore = useChatStore()
const isDarkMode = ref(false)
const isSidebarCollapsed = ref(false)

// 主题相关
const themeIcon = computed(() => isDarkMode.value ? 'fa-sun-o' : 'fa-moon-o')
const themeText = computed(() => isDarkMode.value ? 'Light Mode' : 'Dark Mode')

// 检查Chat是否激活
const isActive = (conversationId) => {
  return chatStore.currentConversation?.id === conversationId
}

// New Chat
const handleNewConversation = () => {
  chatStore.newConversation()
  ElMessage.success('New conversation created')
}

// 选择Chat
const handleSelectConversation = (conversation) => {
  chatStore.currentConversation = conversation
  chatStore.messages = conversation.messages || []
}

// Delete Conversation
const handleDeleteConversation = async (conversation) => {
  try {
    await ElMessageBox.confirm(
      `Are you sure you want to delete "${conversation.title}"? This action cannot be undone.`,
      'Confirm Delete',
      {
        confirmButtonText: 'Delete',
        cancelButtonText: 'Cancel',
        type: 'warning'
      }
    )

    const index = chatStore.conversations.findIndex(c => c.id === conversation.id)
    if (index > -1) {
      chatStore.conversations.splice(index, 1)
      
      if (chatStore.currentConversation?.id === conversation.id) {
        chatStore.newConversation()
      }
      
      ElMessage.success('Conversation deleted')
    }
  } catch {
    // 用户CancelDelete
  }
}

// 切换主题
const toggleTheme = () => {
  isDarkMode.value = !isDarkMode.value
  // 这里可以添加Theme Toggle逻辑
  ElMessage.info(`${themeText.value} activated`)
}

// 切换侧边栏
const toggleSidebar = () => {
  isSidebarCollapsed.value = !isSidebarCollapsed.value
  // 这里可以添加侧边栏切换逻辑
  ElMessage.info(isSidebarCollapsed.value ? 'Sidebar collapsed' : 'Sidebar expanded')
}

// 格式化时间
const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date
  
  if (date.toDateString() === now.toDateString()) {
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  }
  
  const yesterday = new Date(now)
  yesterday.setDate(yesterday.getDate() - 1)
  if (date.toDateString() === yesterday.toDateString()) {
    return 'Yesterday'
  }
  
  if (diff < 7 * 24 * 60 * 60 * 1000) {
    const days = Math.floor(diff / (24 * 60 * 60 * 1000))
    return `${days}d ago`
  }
  
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric'
  })
}
</script>

<style scoped>
.conversation-history {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: white;
}

.search-section {
  padding: 16px;
  border-bottom: 1px solid #e5e7eb;
}

.search-input {
  width: 100%;
  padding: 10px 16px 10px 40px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  background: #f9fafb;
  transition: all 0.3s;
}

.search-input:focus {
  outline: none;
  border-color: #10a37f;
  background: white;
  box-shadow: 0 0 0 3px rgba(16, 163, 127, 0.1);
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #6b7280;
}

.new-conversation-section {
  padding: 0 16px 16px;
}

.new-conversation-btn {
  width: 100%;
  padding: 10px 16px;
  background: #10a37f;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.new-conversation-btn:hover {
  background: #0d8c6c;
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 8px;
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.count {
  color: #9ca3af;
  font-weight: normal;
}

.loading-section {
  padding: 8px;
}

.skeleton-item {
  height: 60px;
  background: #f3f4f6;
  border-radius: 8px;
  margin-bottom: 8px;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.conversations {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.conversation-item {
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  border: 1px solid transparent;
}

.conversation-item:hover {
  background: #f9fafb;
  border-color: #e5e7eb;
}

.conversation-item.active {
  background: #f0fdf4;
  border-color: #10a37f;
}

.conversation-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 6px;
}

.conversation-title {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.conversation-title i {
  color: #6b7280;
  font-size: 12px;
}

.title-text {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.4;
}

.conversation-actions {
  opacity: 0;
  transition: opacity 0.3s;
}

.conversation-item:hover .conversation-actions {
  opacity: 1;
}

.delete-btn {
  background: none;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.3s;
}

.delete-btn:hover {
  color: #ef4444;
  background: #fef2f2;
}

.conversation-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
  color: #9ca3af;
}

.time {
  font-size: 10px;
}

.message-count {
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 6px;
  font-size: 10px;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #6b7280;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  color: #d1d5db;
}

.empty-text {
  font-size: 16px;
  margin-bottom: 8px;
  color: #374151;
}

.empty-subtext {
  font-size: 14px;
  color: #9ca3af;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid #e5e7eb;
}

.footer-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.footer-btn {
  background: none;
  border: none;
  color: #6b7280;
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}

.footer-btn:hover {
  color: #374151;
  background: #f3f4f6;
}

/* 滚动条样式 */
.conversation-list::-webkit-scrollbar {
  width: 4px;
}

.conversation-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 2px;
}

.conversation-list::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 2px;
}

.conversation-list::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .conversation-item {
    padding: 10px;
  }
  
  .conversation-actions {
    opacity: 1;
  }
}
</style>