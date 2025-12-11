// main.js
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './style.css'

// 添加 Font Awesome 样式
import 'font-awesome/css/font-awesome.min.css'

// 全局Error处理
import { setupErrorHandlers } from './plugins/errorHandler'

// 创建 Pinia 实例
const pinia = createPinia()
const app = createApp(App)

// Settings全局Error处理器
setupErrorHandlers(app)

// 使用 Pinia 和 Router
app.use(pinia)
app.use(router)

// 初始化认证Status（需要在 Pinia 之后）
import { useAuthStore } from './stores/auth'
const authStore = useAuthStore()
authStore.initAuth()

app.mount('#app')