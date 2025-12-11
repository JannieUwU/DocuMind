<template>
  <div class="not-found-container">
    <div class="not-found-content">
      <h1 class="error-code">404</h1>
      <h2 class="error-message">页面不存在</h2>
      <p class="error-desc">您访问的页面可能已被Delete或路径Error</p>
      <router-link to="/" class="back-btn">Back to Home</router-link>
    </div>
  </div>
</template>

<script setup></script>

<style scoped>
.not-found-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #f5f7fa;
}
.not-found-content {
  text-align: center;
  background: #fff;
  padding: 50px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
}
.error-code {
  font-size: 80px;
  color: #409eff;
  margin-bottom: 20px;
}
.error-message {
  font-size: 24px;
  color: #1d2129;
  margin-bottom: 10px;
}
.error-desc {
  font-size: 16px;
  color: #4e5969;
  margin-bottom: 30px;
}
.back-btn {
  display: inline-block;
  padding: 12px 24px;
  background: #409eff;
  color: #fff;
  border-radius: 6px;
  text-decoration: none;
  font-size: 16px;
  transition: background 0.3s;
}
.back-btn:hover {
  background: #3086e0;
}
</style>