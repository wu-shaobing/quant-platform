/**
 * 主题相关组合式函数
 */
import { ref, computed, watch, onMounted } from 'vue'
import { STORAGE_KEYS } from '@/utils/constants'

type ThemeMode = 'light' | 'dark' | 'auto'

export const useTheme = () => {
  const currentTheme = ref<ThemeMode>('auto')
  const systemTheme = ref<'light' | 'dark'>('light')
  
  // 计算当前实际主题
  const actualTheme = computed(() => {
    if (currentTheme.value === 'auto') {
      return systemTheme.value
    }
    return currentTheme.value
  })
  
  const isDark = computed(() => actualTheme.value === 'dark')
  
  /**
   * 检测系统主题
   */
  const detectSystemTheme = () => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    systemTheme.value = mediaQuery.matches ? 'dark' : 'light'
    return systemTheme.value
  }
  
  /**
   * 应用主题
   */
  const applyTheme = (theme: 'light' | 'dark') => {
    const root = document.documentElement
    const body = document.body
    
    if (theme === 'dark') {
      root.classList.add('dark')
      body.classList.add('dark')
    } else {
      root.classList.remove('dark')
      body.classList.remove('dark')
    }
    
    // 更新Element Plus主题
    if (theme === 'dark') {
      root.style.colorScheme = 'dark'
    } else {
      root.style.colorScheme = 'light'
    }
  }
  
  /**
   * 切换主题
   */
  const toggleTheme = () => {
    const themes: ThemeMode[] = ['light', 'dark', 'auto']
    const currentIndex = themes.indexOf(currentTheme.value)
    const nextIndex = (currentIndex + 1) % themes.length
    setTheme(themes[nextIndex])
  }
  
  /**
   * 设置主题
   */
  const setTheme = (theme: ThemeMode) => {
    currentTheme.value = theme
    localStorage.setItem(STORAGE_KEYS.THEME, theme)
  }
  
  /**
   * 获取主题图标
   */
  const getThemeIcon = computed(() => {
    switch (currentTheme.value) {
      case 'light':
        return 'Sunny'
      case 'dark':
        return 'Moon'
      case 'auto':
        return 'Monitor'
      default:
        return 'Monitor'
    }
  })
  
  /**
   * 获取主题标签
   */
  const getThemeLabel = computed(() => {
    switch (currentTheme.value) {
      case 'light':
        return '浅色模式'
      case 'dark':
        return '深色模式'
      case 'auto':
        return '跟随系统'
      default:
        return '跟随系统'
    }
  })
  
  /**
   * 初始化主题
   */
  const initTheme = () => {
    // 从本地存储恢复主题设置
    const savedTheme = localStorage.getItem(STORAGE_KEYS.THEME) as ThemeMode
    if (savedTheme && ['light', 'dark', 'auto'].includes(savedTheme)) {
      currentTheme.value = savedTheme
    }
    
    // 检测系统主题
    detectSystemTheme()
    
    // 监听系统主题变化
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    mediaQuery.addEventListener('change', (e) => {
      systemTheme.value = e.matches ? 'dark' : 'light'
    })
    
    // 应用初始主题
    applyTheme(actualTheme.value)
  }
  
  // 监听主题变化
  watch(actualTheme, (newTheme) => {
    applyTheme(newTheme)
  })
  
  // 组件挂载时初始化
  onMounted(() => {
    initTheme()
  })
  
  return {
    currentTheme: readonly(currentTheme),
    actualTheme,
    isDark,
    systemTheme: readonly(systemTheme),
    getThemeIcon,
    getThemeLabel,
    toggleTheme,
    setTheme,
    initTheme
  }
}