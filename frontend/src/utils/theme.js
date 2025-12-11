// src/utils/theme.js
import storage from '@/services/storage.service'

export const themeConfig = {
  light: {
    primary: '#3B82F6',
    background: '#FFFFFF',
    surface: '#F9FAFB',
    surfaceElevated: '#FFFFFF',
    text: {
      primary: '#1F2937',
      secondary: '#6B7280',
      tertiary: '#9CA3AF'
    },
    border: {
      light: '#E5E7EB',
      medium: '#D1D5DB',
      strong: '#9CA3AF'
    }
  },
  dark: {
    primary: '#60A5FA',
    background: '#111827',
    surface: '#1F2937',
    surfaceElevated: '#374151',
    text: {
      primary: '#F9FAFB',
      secondary: '#D1D5DB',
      tertiary: '#9CA3AF'
    },
    border: {
      light: '#374151',
      medium: '#4B5563',
      strong: '#6B7280'
    }
  }
}

class ThemeManager {
  constructor() {
    this.currentTheme = 'dark' // 默认暗色
  }

  initTheme() {
    // 从 localStorage 读取或使用默认值
    const savedTheme = storage.get('dashboard-theme', 'dark')
    this.applyTheme(savedTheme)
  }

  applyTheme(theme) {
    this.currentTheme = theme
    const html = document.documentElement
    
    // Apply主题类
    if (theme === 'dark') {
      html.classList.add('dark')
      html.classList.remove('light')
    } else {
      html.classList.add('light')
      html.classList.remove('dark')
    }
    
    // Settings CSS 自定义属性
    this.setCSSVariables(theme)

    // Save到 localStorage
    storage.set('dashboard-theme', theme)

    // 触发主题变化事件
    window.dispatchEvent(new CustomEvent('themechange', { detail: theme }))
  }

  setCSSVariables(theme) {
    const root = document.documentElement
    const config = themeConfig[theme]
    
    // Settings颜色变量
    Object.entries(config).forEach(([key, value]) => {
      if (typeof value === 'object') {
        Object.entries(value).forEach(([subKey, subValue]) => {
          root.style.setProperty(`--${key}-${subKey}`, subValue)
        })
      } else {
        root.style.setProperty(`--${key}`, value)
      }
    })
  }

  toggleTheme() {
    const newTheme = this.currentTheme === 'dark' ? 'light' : 'dark'
    this.applyTheme(newTheme)
    return newTheme
  }

  getCurrentTheme() {
    return this.currentTheme
  }
}

// 创建单例实例
export const themeManager = new ThemeManager()