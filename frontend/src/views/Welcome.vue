<template>
  <div class="welcome-container" :class="{ 'transition-active': isTransitioning }">
    <AuroraBackground>
      <div class="relative flex flex-col items-center justify-center gap-4 px-4">
        <div class="text-center text-3xl font-bold md:text-7xl text-black">
          Welcome to use RAG Hybrid Search
        </div>
        <div class="py-4 text-base font-extralight md:text-4xl text-gray-800">
          Enjoy your personalized experience.
        </div>
        <button
          @click="startTransition"
          class="start-btn"
          :class="{ 'btn-expanding': isTransitioning }"
        >
          <span class="btn-text" :class="{ 'text-hidden': isTransitioning }">Start!</span>
        </button>
      </div>
    </AuroraBackground>
    
    <!-- 黑色遮罩层 -->
    <div class="black-overlay" :class="{ 'overlay-active': isTransitioning }"></div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import AuroraBackground from '@/components/AuroraBackground.vue'

const router = useRouter()
const isTransitioning = ref(false)

const startTransition = () => {
  isTransitioning.value = true
  
  // 动画持续时间与 CSS 中定义的保持一致
  setTimeout(() => {
    router.push('/login')
  }, 1000) // 1秒后跳转，与动画持续时间匹配
}
</script>

<style scoped>
.welcome-container {
  position: relative;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}

.black-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: black;
  opacity: 0;
  z-index: 20;
  pointer-events: none;
  transition: opacity 0.8s ease;
}

.overlay-active {
  opacity: 1;
}

.start-btn {
  width: fit-content;
  background: black;
  color: white;
  border: none;
  border-radius: 50px;
  padding: 12px 32px;
  font-size: 1.125rem;
  cursor: pointer;
  transition: all 0.8s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  z-index: 30;
  display: flex;
  align-items: center;
  justify-content: center;
}

.start-btn:hover:not(.btn-expanding) {
  background: rgba(0, 0, 0, 0.8);
  transform: translateY(-2px);
}

.btn-expanding {
  transform: scale(20) !important;
  background: black !important;
}

.btn-text {
  transition: opacity 0.2s ease;
}

.text-hidden {
  opacity: 0 !important;
}

/* 确保 AuroraBackground 在过渡期间保持在正确层级 */
.welcome-container :deep(.aurora-background) {
  position: relative;
  z-index: 10;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .start-btn {
    padding: 10px 24px;
    font-size: 1rem;
  }
  
  .btn-expanding {
    transform: scale(15) !important;
  }
}
</style>