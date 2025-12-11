import { createRouter, createWebHashHistory } from 'vue-router'
import Welcome from '@/views/Welcome.vue'
import Login from '@/views/Login.vue'
import Register from '@/views/Register.vue'
import ResetPassword from '@/views/ResetPassword.vue'
import Dashboard from '@/views/Dashboard.vue'
import NotFound from '@/views/NotFound.vue'
import storage from '@/services/storage.service'
import secureStorage from '@/services/secureStorage.service'

const routes = [
  {
    path: '/',
    name: 'Welcome',
    component: Welcome,
    meta: { requiresGuest: true, title: 'Welcome' }
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresGuest: true, title: 'Login' }
  },
  {
    path: '/register',
    name: 'Register',
    component: Register,
    meta: { requiresGuest: true, title: 'Register' }
  },
  {
    path: '/reset-password',
    name: 'ResetPassword',
    component: ResetPassword,
    meta: { requiresGuest: true, title: 'Reset Password' }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
    meta: { requiresAuth: true, title: '首页' }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: NotFound,
    meta: { title: '页面不存在' }
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  // Check for token in secure storage or legacy storage
  const hasSecureToken = secureStorage.hasSecure('token')
  const hasLegacyToken = storage.has('token')
  const isAuthenticated = hasSecureToken || hasLegacyToken

  // Settings页面Title
  if (to.meta.title) {
    document.title = `${to.meta.title} - RAG Hybrid Search`
  }

  if (to.meta.requiresAuth && !isAuthenticated) {
    // 需要Login但未Login，跳转到Login页
    next('/login')
  } else if (to.meta.requiresGuest && isAuthenticated) {
    // 需要游客Status但已Login，跳转到仪表板
    next('/dashboard')
  } else {
    // 正常放行
    next()
  }
})

// 路由Error处理
router.onError((error) => {
  console.error('路由Error:', error)
})

export default router