<template>
  <div class="spline-container">
    <div class="spline-overlay">
      <span class="logo-text">RAG Hybrid Search</span>
      <span class="slogan-text">Intelligent Search with AI Power</span>
    </div>
    <div class="spline-wrapper">
      <Spline
        :scene="sceneUrl"
        class="spline-element"
      />
    </div>
  </div>
</template>

<script setup>
import Spline from './Spline.vue'

const sceneUrl = "https://prod.spline.design/kZDDjO5HuC9GJUM2/scene.splinecode";
</script>

<style scoped>
.spline-container {
  position: relative;
  width: 100%;
  height: 100%;
  background: black;
  overflow: hidden;
}

.spline-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  z-index: 10;
  pointer-events: none;
}

.logo-text {
  font-size: 2.5rem;
  font-weight: 600;
  color: white;
  margin-bottom: 1rem;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
}

.slogan-text {
  font-size: 1.1rem;
  font-weight: 300;
  color: rgba(255, 255, 255, 0.8);
  text-shadow: 0 1px 5px rgba(0, 0, 0, 0.5);
}

.spline-wrapper {
  width: 100%;
  height: 100%;
}

.spline-element {
  width: 100%;
  height: 100%;
}

@media (max-width: 768px) {
  .logo-text {
    font-size: 2rem;
  }
  
  .slogan-text {
    font-size: 1rem;
  }
}
</style>