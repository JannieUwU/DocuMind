<!--
  ParagraphInteraction Component

  Intelligent Paragraph Interaction System - Provides source, explanation, and search features for each paragraph of AI responses
-->
<template>
  <div
    class="paragraph-wrapper"
    @mouseenter="handleMouseEnter"
    @mouseleave="handleMouseLeave"
    :class="{ 'is-active': isActive }"
  >
    <!-- Paragraph Content -->
    <div
      class="paragraph-content"
      v-html="content"
    ></div>

    <!-- Right Side Action Buttons -->
    <transition name="fade-slide">
      <div v-if="isActive" class="action-buttons">
        <!-- Source Button -->
        <button
          v-if="hasSource"
          @click="showSourceInfo"
          class="action-btn source-btn"
          title="View Source"
        >
          <i class="fa fa-file-text-o"></i>
        </button>

        <!-- Explain Button -->
        <button
          @click="explainParagraph"
          class="action-btn explain-btn"
          title="AI Explain This Content"
        >
          <i class="fa fa-question-circle-o"></i>
        </button>

        <!-- Search Button -->
        <button
          @click="searchParagraph"
          class="action-btn search-btn"
          title="Search This Content"
        >
          <i class="fa fa-search"></i>
        </button>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  // Paragraph HTML content
  content: {
    type: String,
    required: true
  },
  // Paragraph plain text (for search and explanation)
  text: {
    type: String,
    required: true
  },
  // Source information
  source: {
    type: Object,
    default: null
    // Format: { documentName, page, position, preview }
  },
  // Whether to use dark theme
  isDark: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits([
  'show-source',    // Show source information
  'explain',        // Request explanation
  'search'          // Search content
])

const isActive = ref(false)

// Whether has source information
const hasSource = computed(() => {
  return props.source && props.source.documentName
})

// Mouse enter
const handleMouseEnter = () => {
  isActive.value = true
}

// Mouse leave
const handleMouseLeave = () => {
  isActive.value = false
}

// Show source information
const showSourceInfo = () => {
  emit('show-source', {
    text: props.text,
    source: props.source
  })
}

// Explain paragraph
const explainParagraph = () => {
  emit('explain', props.text)
}

// Search paragraph
const searchParagraph = () => {
  emit('search', props.text)
}
</script>

<style scoped>
.paragraph-wrapper {
  position: relative;
  padding: 12px 60px 12px 16px;
  margin: 8px 0;
  border-radius: 8px;
  transition: all 0.3s ease;
  cursor: pointer;
}

.paragraph-wrapper:hover {
  background-color: rgba(0, 0, 0, 0.02);
}

.dark .paragraph-wrapper:hover {
  background-color: rgba(255, 255, 255, 0.05);
}

.paragraph-wrapper.is-active {
  background-color: rgba(59, 130, 246, 0.05);
  border: 1px solid rgba(59, 130, 246, 0.2);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
}

.dark .paragraph-wrapper.is-active {
  background-color: rgba(96, 165, 250, 0.08);
  border-color: rgba(96, 165, 250, 0.3);
  box-shadow: 0 2px 8px rgba(96, 165, 250, 0.15);
}

.paragraph-content {
  line-height: 1.6;
  color: inherit;
}

/* Right Side Action Buttons */
.action-buttons {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column;
  gap: 6px;
  z-index: 10;
}

.action-btn {
  width: 36px;
  height: 36px;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
  background-color: #ffffff;
  color: #6b7280;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 16px;
}

.action-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.action-btn:active {
  transform: scale(0.95);
}

/* Source Button */
.source-btn {
  border-color: #10b981;
  color: #10b981;
}

.source-btn:hover {
  background-color: #10b981;
  color: #ffffff;
}

/* Explain Button */
.explain-btn {
  border-color: #3b82f6;
  color: #3b82f6;
}

.explain-btn:hover {
  background-color: #3b82f6;
  color: #ffffff;
}

/* Search Button */
.search-btn {
  border-color: #f59e0b;
  color: #f59e0b;
}

.search-btn:hover {
  background-color: #f59e0b;
  color: #ffffff;
}

/* Dark Theme Button Styles */
.dark .action-btn {
  background-color: #374151;
  border-color: #4b5563;
  color: #9ca3af;
}

.dark .action-btn:hover {
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
}

.dark .source-btn {
  border-color: #10b981;
  color: #10b981;
}

.dark .source-btn:hover {
  background-color: #10b981;
  color: #ffffff;
}

.dark .explain-btn {
  border-color: #60a5fa;
  color: #60a5fa;
}

.dark .explain-btn:hover {
  background-color: #3b82f6;
  color: #ffffff;
}

.dark .search-btn {
  border-color: #fbbf24;
  color: #fbbf24;
}

.dark .search-btn:hover {
  background-color: #f59e0b;
  color: #ffffff;
}

/* Fade Slide Animation */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateX(10px) translateY(-50%);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateX(10px) translateY(-50%);
}
</style>
