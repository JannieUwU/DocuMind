<template>
  <div class="register-container" :class="{ 'register-visible': isVisible }">
    <AuroraBackground>
      <div class="register-wrapper">
        <!-- Register Card -->
        <div class="register-card">
          <h2 class="register-title">Create Account</h2>
          <form @submit.prevent="handleRegister" class="register-form">
            <!-- Username -->
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

            <!-- Email -->
            <div class="form-group">
              <label>Email</label>
              <div class="input-with-button">
                <input
                  type="email"
                  v-model.trim="email"
                  placeholder="Enter your email"
                  class="form-input"
                  :class="{ error: formErrors.email }"
                />
                <button
                  type="button"
                  class="send-code-btn"
                  :disabled="codeSending || countdown > 0"
                  @click="sendCode"
                >
                  <span v-if="codeSending">Sending...</span>
                  <span v-else-if="countdown > 0">{{ countdown }}s</span>
                  <span v-else>Send Code</span>
                </button>
              </div>
              <p class="error-text">{{ formErrors.email }}</p>
            </div>

            <!-- Verification Code -->
            <div class="form-group">
              <label>Verification Code</label>
              <input
                type="text"
                v-model.trim="verificationCode"
                placeholder="Enter 6-digit code"
                class="form-input"
                :class="{ error: formErrors.verificationCode }"
                maxlength="6"
              />
              <p class="error-text">{{ formErrors.verificationCode }}</p>
            </div>

            <!-- Password -->
            <div class="form-group">
              <label>Password</label>
              <input
                type="password"
                v-model.trim="password"
                placeholder="Enter your password"
                class="form-input"
                :class="{ error: formErrors.password }"
              />
              <p class="password-hint">At least 6 characters with uppercase, lowercase, and numbers</p>
              <p class="error-text">{{ formErrors.password }}</p>
            </div>

            <!-- Confirm Password -->
            <div class="form-group">
              <label>Confirm Password</label>
              <input
                type="password"
                v-model.trim="confirmPassword"
                placeholder="Confirm your password"
                class="form-input"
                :class="{ error: formErrors.confirmPassword }"
              />
              <p class="error-text">{{ formErrors.confirmPassword }}</p>
            </div>

            <p class="global-error" v-if="globalError">{{ globalError }}</p>

            <button type="submit" class="register-btn" :disabled="isLoading">
              <span v-if="isLoading">Registering...</span>
              <span v-else>Register</span>
            </button>

            <div class="login-link">
              Already have an account? <router-link to="/login">Sign in</router-link>
            </div>
          </form>
        </div>
      </div>
    </AuroraBackground>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AuroraBackground from '@/components/AuroraBackground.vue'

const router = useRouter()
const authStore = useAuthStore()
const username = ref('')
const email = ref('')
const verificationCode = ref('')
const password = ref('')
const confirmPassword = ref('')
const isLoading = ref(false)
const codeSending = ref(false)
const countdown = ref(0)
const globalError = ref('')
const formErrors = ref({})
const isVisible = ref(false)

onMounted(() => {
  setTimeout(() => {
    isVisible.value = true
  }, 100)
})

// Send verification code
const sendCode = async () => {
  formErrors.value.email = ''

  if (!email.value.trim()) {
    formErrors.value.email = 'Email is required'
    return
  }

  if (!email.value.includes('@')) {
    formErrors.value.email = 'Please enter a valid email'
    return
  }

  try {
    codeSending.value = true
    const res = await authStore.sendVerificationCode(email.value)
    if (res.success) {
      // Start countdown
      countdown.value = 60
      const timer = setInterval(() => {
        countdown.value--
        if (countdown.value <= 0) {
          clearInterval(timer)
        }
      }, 1000)
    } else {
      formErrors.value.email = res.error
    }
  } catch (err) {
    formErrors.value.email = 'Failed to send code'
    console.error('Send code failed:', err)
  } finally {
    codeSending.value = false
  }
}

// Register
const handleRegister = async () => {
  globalError.value = ''
  formErrors.value = {}
  let isValid = true

  if (!username.value.trim()) {
    formErrors.value.username = 'Username is required'
    isValid = false
  } else if (username.value.length < 3) {
    formErrors.value.username = 'Username must be at least 3 characters'
    isValid = false
  }

  if (!email.value.trim()) {
    formErrors.value.email = 'Email is required'
    isValid = false
  } else if (!email.value.includes('@')) {
    formErrors.value.email = 'Please enter a valid email'
    isValid = false
  }

  if (!verificationCode.value.trim()) {
    formErrors.value.verificationCode = 'Verification code is required'
    isValid = false
  } else if (verificationCode.value.length !== 6) {
    formErrors.value.verificationCode = 'Code must be 6 digits'
    isValid = false
  }

  if (!password.value.trim()) {
    formErrors.value.password = 'Password is required'
    isValid = false
  } else if (password.value.length < 6) {
    formErrors.value.password = 'Password must be at least 6 characters'
    isValid = false
  } else if (!/[A-Z]/.test(password.value)) {
    formErrors.value.password = 'Password must contain at least one uppercase letter'
    isValid = false
  } else if (!/[a-z]/.test(password.value)) {
    formErrors.value.password = 'Password must contain at least one lowercase letter'
    isValid = false
  } else if (!/[0-9]/.test(password.value)) {
    formErrors.value.password = 'Password must contain at least one number'
    isValid = false
  }

  if (!confirmPassword.value.trim()) {
    formErrors.value.confirmPassword = 'Please confirm your password'
    isValid = false
  } else if (password.value !== confirmPassword.value) {
    formErrors.value.confirmPassword = 'Passwords do not match'
    isValid = false
  }

  if (!isValid) return

  try {
    isLoading.value = true
    const res = await authStore.register(username.value, email.value, password.value, verificationCode.value)
    if (res.success) {
      router.push('/login')
    } else {
      globalError.value = res.error
    }
  } catch (err) {
    globalError.value = 'Network error, please try again'
    console.error('Register failed:', err)
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.register-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  opacity: 0;
  transition: opacity 0.8s ease;
  overflow-y: auto;
}

.register-visible {
  opacity: 1;
}

.register-wrapper {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.register-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 30px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.3);
  max-height: 90vh;
  overflow-y: auto;
}

/* Dark mode styles */
:global(body.dark-mode) .register-card {
  background: rgba(30, 30, 30, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.register-title {
  text-align: center;
  color: #1a1a1a;
  margin-bottom: 20px;
  font-size: 24px;
  font-weight: 600;
}

:global(body.dark-mode) .register-title {
  color: #ffffff;
}

.form-group {
  margin-bottom: 14px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  color: #333;
  font-size: 13px;
  font-weight: 500;
}

:global(body.dark-mode) .form-group label {
  color: #e0e0e0;
}

.form-input {
  width: 100%;
  padding: 10px 14px;
  border: 2px solid #e0e0e0;
  border-radius: 10px;
  font-size: 14px;
  transition: all 0.3s;
  background: white;
  color: #333;
}

:global(body.dark-mode) .form-input {
  background: rgba(50, 50, 50, 0.8);
  border: 2px solid rgba(255, 255, 255, 0.1);
  color: #ffffff;
}

.form-input::placeholder {
  color: #999;
}

:global(body.dark-mode) .form-input::placeholder {
  color: #666;
}

.form-input:focus {
  outline: none;
  border-color: #333;
  box-shadow: 0 0 0 3px rgba(0, 0, 0, 0.05);
}

:global(body.dark-mode) .form-input:focus {
  border-color: #ffffff;
  box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.1);
}

.form-input.error {
  border-color: #f56c6c;
}

.input-with-button {
  display: flex;
  gap: 10px;
}

.input-with-button .form-input {
  flex: 1;
}

.send-code-btn {
  padding: 10px 16px;
  background: #1a1a1a;
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  white-space: nowrap;
  min-width: 100px;
}

:global(body.dark-mode) .send-code-btn {
  background: #ffffff;
  color: #1a1a1a;
}

.send-code-btn:hover:not(:disabled) {
  background: #333;
}

:global(body.dark-mode) .send-code-btn:hover:not(:disabled) {
  background: #e0e0e0;
}

.send-code-btn:disabled {
  background: #ccc;
  color: #666;
  cursor: not-allowed;
}

:global(body.dark-mode) .send-code-btn:disabled {
  background: rgba(100, 100, 100, 0.5);
  color: #888;
}

.password-hint {
  margin-top: 4px;
  font-size: 11px;
  color: #666;
  line-height: 1.3;
}

:global(body.dark-mode) .password-hint {
  color: #999;
}

.error-text {
  margin-top: 4px;
  font-size: 11px;
  color: #f56c6c;
  height: 14px;
}

.global-error {
  margin: 12px 0;
  padding: 10px;
  background: rgba(245, 108, 108, 0.1);
  border-radius: 8px;
  font-size: 13px;
  color: #f56c6c;
  text-align: center;
  border: 1px solid rgba(245, 108, 108, 0.3);
}

.register-btn {
  width: 100%;
  padding: 12px;
  background: #1a1a1a;
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  margin-top: 6px;
}

:global(body.dark-mode) .register-btn {
  background: #ffffff;
  color: #1a1a1a;
}

.register-btn:hover:not(:disabled) {
  background: #333;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

:global(body.dark-mode) .register-btn:hover:not(:disabled) {
  background: #e0e0e0;
  box-shadow: 0 4px 12px rgba(255, 255, 255, 0.2);
}

.register-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

:global(body.dark-mode) .register-btn:disabled {
  background: rgba(100, 100, 100, 0.5);
  color: #888;
}

.login-link {
  margin-top: 16px;
  text-align: center;
  font-size: 13px;
  color: #666;
}

:global(body.dark-mode) .login-link {
  color: #999;
}

.login-link a {
  color: #1a1a1a;
  text-decoration: none;
  margin-left: 4px;
  font-weight: 600;
}

:global(body.dark-mode) .login-link a {
  color: #ffffff;
}

.login-link a:hover {
  text-decoration: underline;
}

/* Responsive */
@media (max-width: 768px) {
  .register-wrapper {
    padding: 20px 15px;
  }

  .register-card {
    padding: 30px 20px;
  }

  .register-title {
    font-size: 24px;
    margin-bottom: 20px;
  }

  .form-group {
    margin-bottom: 16px;
  }

  .input-with-button {
    flex-direction: column;
  }

  .send-code-btn {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .register-wrapper {
    padding: 15px 10px;
  }

  .register-card {
    padding: 25px 15px;
    border-radius: 15px;
  }

  .register-title {
    font-size: 22px;
    margin-bottom: 15px;
  }

  .form-group {
    margin-bottom: 14px;
  }

  .form-input {
    padding: 10px 14px;
    font-size: 14px;
  }

  .password-hint {
    font-size: 11px;
  }

  .error-text {
    font-size: 11px;
  }
}

/* Large screen optimization */
@media (min-width: 1440px) {
  .register-card {
    max-width: 440px;
    padding: 35px;
  }

  .register-title {
    font-size: 26px;
    margin-bottom: 24px;
  }

  .form-group {
    margin-bottom: 16px;
  }
}
</style>
