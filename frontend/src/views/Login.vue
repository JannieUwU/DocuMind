<template>
  <div class="login-container" :class="{ 'login-visible': isVisible }">
    <div class="login-layout">
      <!-- 左侧 Spline 动画区域 -->
      <div class="spline-section">
        <SplineAnimation />
      </div>

      <!-- 右侧Login表单区域 -->
      <div class="form-section">
        <div class="login-card">
          <h2 class="login-title">User Login</h2>
          <form @submit.prevent="handleLogin" class="login-form">
            <div class="form-group">
              <label>Username</label>
              <input
                type="text"
                v-model.trim="username"
                placeholder="Enter your username"
                class="form-input"
                :class="{ error: formErrors.username }"
              />
              <p class="error-text">{{ formErrors.username }}</p>
            </div>
            <div class="form-group">
              <label>Password</label>
              <input
                type="password"
                v-model.trim="password"
                placeholder="Enter your password"
                class="form-input"
                :class="{ error: formErrors.password }"
              />
              <p class="error-text">{{ formErrors.password }}</p>
            </div>
            <p class="global-error" v-if="globalError">{{ globalError }}</p>
            <button type="submit" class="login-btn" :disabled="isLoading">
              <span v-if="isLoading">Logging in...</span>
              <span v-else>Login</span>
            </button>
            <div class="forgot-password-link">
              <router-link to="/reset-password">Forgot password?</router-link>
            </div>
            <div class="register-link">
              Don't have an account? <router-link to="/register">Sign up</router-link>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import SplineAnimation from '@/components/SplineAnimation.vue'

const router = useRouter()
const authStore = useAuthStore()
const username = ref('')
const password = ref('')
const isLoading = ref(false)
const globalError = ref('')
const formErrors = ref({})
const isVisible = ref(false)

onMounted(() => {
  // 页面加载后立即开始进入动画
  setTimeout(() => {
    isVisible.value = true
  }, 100)
})

const handleLogin = async () => {
  globalError.value = ''
  formErrors.value = {}
  let isValid = true

  if (!username.value.trim()) {
    formErrors.value.username = 'Username is required'
    isValid = false
  }
  if (!password.value.trim()) {
    formErrors.value.password = 'Password is required'
    isValid = false
  }

  if (!isValid) return

  try {
    isLoading.value = true
    const res = await authStore.login(username.value, password.value)

    // 只有明确Success时才跳转
    if (res && res.success === true) {
      router.push('/dashboard')
    } else {
      // LoginFailed，显示ErrorInformation，不跳转
      globalError.value = res?.error || 'Invalid username or password'
    }
  } catch (err) {
    // 捕获所有Error，显示ErrorInformation，不跳转
    globalError.value = err?.message || 'Network error, please try again'
    console.error('Login failed:', err)
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  background: black;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  opacity: 0;
  transform: translateY(20px);
  transition: all 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

.login-visible {
  opacity: 1;
  transform: translateY(0);
}

.login-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  max-width: 1200px;
  width: 100%;
  background: black;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(255, 255, 255, 0.1);
  overflow: hidden;
  min-height: 700px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.spline-section {
  background: black;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.form-section {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background: black;
}

.login-card {
  width: 100%;
  max-width: 400px;
  opacity: 0;
  transform: translateY(10px);
  transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1) 0.3s;
}

.login-visible .login-card {
  opacity: 1;
  transform: translateY(0);
}

.login-title {
  text-align: center;
  color: white;
  margin-bottom: 40px;
  font-size: 28px;
  font-weight: 600;
}

.form-group {
  margin-bottom: 24px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
  font-weight: 500;
}

.form-input {
  width: 100%;
  padding: 14px 16px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 10px;
  font-size: 16px;
  transition: all 0.3s;
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.form-input::placeholder {
  color: rgba(255, 255, 255, 0.5);
}

.form-input:focus {
  outline: none;
  border-color: #409eff;
  background: rgba(255, 255, 255, 0.15);
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.1);
}

.form-input.error {
  border-color: #f56c6c;
}

.error-text {
  margin-top: 6px;
  font-size: 12px;
  color: #f56c6c;
  height: 18px;
}

.global-error {
  margin: 16px 0;
  padding: 12px;
  background: rgba(245, 108, 108, 0.1);
  border-radius: 8px;
  font-size: 14px;
  color: #f56c6c;
  text-align: center;
  border: 1px solid rgba(245, 108, 108, 0.3);
}

.login-btn {
  width: 100%;
  padding: 14px;
  background: white;
  color: black !important;
  border: none;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  margin-top: 8px;
}

.login-btn span {
  color: black !important;
}

.login-btn:disabled {
  background: rgba(255, 255, 255, 0.5);
  color: rgba(0, 0, 0, 0.5) !important;
  cursor: not-allowed;
}

.login-btn:disabled span {
  color: rgba(0, 0, 0, 0.5) !important;
}

.login-btn:hover:not(:disabled) {
  background: #f0f0f0;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(255, 255, 255, 0.2);
}

.forgot-password-link {
  margin-top: 12px;
  text-align: center;
  font-size: 13px;
}

.forgot-password-link a {
  color: #999;
  text-decoration: none;
  transition: all 0.3s;
}

.forgot-password-link a:hover {
  color: #fff;
  text-decoration: underline;
}

.register-link {
  margin-top: 16px;
  text-align: center;
  font-size: 14px;
  color: #999;
}

.register-link a {
  color: #999;
  text-decoration: none;
  margin-left: 4px;
  font-weight: 500;
}

.register-link a:hover {
  color: #ccc;
  text-decoration: underline;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .login-layout {
    grid-template-columns: 1fr;
    min-height: auto;
  }
  
  .spline-section {
    min-height: 300px;
  }
  
  .form-section {
    padding: 30px 20px;
  }
  
  .login-title {
    font-size: 24px;
    margin-bottom: 30px;
  }
}
</style>