<!--
  StopGenerationButton Component

  Button to cancel ongoing AI response generation.
  Shows only when a request is pending.
-->
<template>
  <transition name="fade">
    <button
      v-if="isLoading"
      @click="handleStop"
      class="stop-button"
      :class="{ 'stop-button-pulsing': isLoading }"
      title="Stop generation"
    >
      <i class="fa fa-stop-circle"></i>
      <span class="ml-2">Stop Generating</span>
    </button>
  </transition>
</template>

<script setup>
import { useChatStore } from '@/stores/chat'
import { computed } from 'vue'
import { ElMessage } from 'element-plus'

const chatStore = useChatStore()

const isLoading = computed(() => chatStore.loading)

/**
 * Handle stop button click
 */
function handleStop() {
  const cancelled = chatStore.cancelCurrentMessage()

  if (cancelled) {
    ElMessage.info('Generation stopped')
  } else {
    ElMessage.warning('No active generation to stop')
  }
}
</script>

<style scoped>
.stop-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background-color: #ef4444;
  color: white;
  border: none;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 4px rgba(239, 68, 68, 0.2);
}

.stop-button:hover {
  background-color: #dc2626;
  transform: translateY(-1px);
  box-shadow: 0 4px 6px rgba(239, 68, 68, 0.3);
}

.stop-button:active {
  transform: translateY(0);
  box-shadow: 0 2px 4px rgba(239, 68, 68, 0.2);
}

.stop-button-pulsing {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.8;
  }
}

/* Fade transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s, transform 0.3s;
}

.fade-enter-from {
  opacity: 0;
  transform: scale(0.95);
}

.fade-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

/* Dark mode */
:global(.dark) .stop-button {
  background-color: #dc2626;
  box-shadow: 0 2px 4px rgba(220, 38, 38, 0.3);
}

:global(.dark) .stop-button:hover {
  background-color: #b91c1c;
  box-shadow: 0 4px 6px rgba(220, 38, 38, 0.4);
}
</style>
