/**
 * 用户体验优化组合函数
 * 包含加载状态、错误处理、用户引导、无障碍功能等
 */

import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElNotification, ElMessageBox } from 'element-plus'

// 加载状态管理
export interface LoadingState {
  isLoading: boolean
  message: string
  progress?: number
}

// 错误状态管理
export interface ErrorState {
  hasError: boolean
  message: string
  code?: string
  details?: any
}

// 用户引导步骤
export interface GuideStep {
  target: string
  title: string
  content: string
  placement?: 'top' | 'bottom' | 'left' | 'right'
  showSkip?: boolean
  onNext?: () => void
  onPrev?: () => void
}

// 通知配置
export interface NotificationConfig {
  title: string
  message: string
  type?: 'success' | 'warning' | 'info' | 'error'
  duration?: number
  showClose?: boolean
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left'
}

// 加载状态管理
export function useLoadingState(initialMessage = '加载中...') {
  const loadingState = ref<LoadingState>({
    isLoading: false,
    message: initialMessage,
    progress: undefined
  })

  const startLoading = (message?: string, progress?: number) => {
    loadingState.value = {
      isLoading: true,
      message: message || initialMessage,
      progress
    }
  }

  const updateProgress = (progress: number, message?: string) => {
    if (loadingState.value.isLoading) {
      loadingState.value.progress = progress
      if (message) {
        loadingState.value.message = message
      }
    }
  }

  const stopLoading = () => {
    loadingState.value.isLoading = false
    loadingState.value.progress = undefined
  }

  const withLoading = async <T>(
    asyncFn: () => Promise<T>,
    message?: string
  ): Promise<T> => {
    startLoading(message)
    try {
      const result = await asyncFn()
      return result
    } finally {
      stopLoading()
    }
  }

  return {
    loadingState: readonly(loadingState),
    isLoading: computed(() => loadingState.value.isLoading),
    loadingMessage: computed(() => loadingState.value.message),
    loadingProgress: computed(() => loadingState.value.progress),
    startLoading,
    updateProgress,
    stopLoading,
    withLoading
  }
}

// 错误处理
export function useErrorHandling() {
  const errorState = ref<ErrorState>({
    hasError: false,
    message: '',
    code: undefined,
    details: undefined
  })

  const setError = (message: string, code?: string, details?: any) => {
    errorState.value = {
      hasError: true,
      message,
      code,
      details
    }

    // 自动显示错误消息
    ElMessage.error({
      message,
      duration: 5000,
      showClose: true
    })
  }

  const clearError = () => {
    errorState.value = {
      hasError: false,
      message: '',
      code: undefined,
      details: undefined
    }
  }

  const handleApiError = (error: any) => {
    let message = '操作失败，请稍后重试'
    let code = 'UNKNOWN_ERROR'

    if (error.response) {
      // HTTP错误
      const status = error.response.status
      const data = error.response.data

      switch (status) {
        case 400:
          message = data.message || '请求参数错误'
          code = 'BAD_REQUEST'
          break
        case 401:
          message = '登录已过期，请重新登录'
          code = 'UNAUTHORIZED'
          break
        case 403:
          message = '没有权限执行此操作'
          code = 'FORBIDDEN'
          break
        case 404:
          message = '请求的资源不存在'
          code = 'NOT_FOUND'
          break
        case 429:
          message = '请求过于频繁，请稍后重试'
          code = 'TOO_MANY_REQUESTS'
          break
        case 500:
          message = '服务器内部错误'
          code = 'INTERNAL_ERROR'
          break
        default:
          message = data.message || `请求失败 (${status})`
          code = `HTTP_${status}`
      }
    } else if (error.request) {
      // 网络错误
      message = '网络连接失败，请检查网络设置'
      code = 'NETWORK_ERROR'
    } else {
      // 其他错误
      message = error.message || '未知错误'
      code = 'UNKNOWN_ERROR'
    }

    setError(message, code, error)
  }

  const withErrorHandling = async <T>(
    asyncFn: () => Promise<T>,
    customErrorHandler?: (error: any) => void
  ): Promise<T | null> => {
    try {
      clearError()
      return await asyncFn()
    } catch (error) {
      if (customErrorHandler) {
        customErrorHandler(error)
      } else {
        handleApiError(error)
      }
      return null
    }
  }

  return {
    errorState: readonly(errorState),
    hasError: computed(() => errorState.value.hasError),
    errorMessage: computed(() => errorState.value.message),
    errorCode: computed(() => errorState.value.code),
    setError,
    clearError,
    handleApiError,
    withErrorHandling
  }
}

// 通知管理
export function useNotifications() {
  const showSuccess = (config: string | NotificationConfig) => {
    if (typeof config === 'string') {
      ElNotification.success({
        title: '成功',
        message: config,
        duration: 3000
      })
    } else {
      ElNotification.success({
        duration: 3000,
        ...config,
        type: 'success'
      })
    }
  }

  const showError = (config: string | NotificationConfig) => {
    if (typeof config === 'string') {
      ElNotification.error({
        title: '错误',
        message: config,
        duration: 5000
      })
    } else {
      ElNotification.error({
        duration: 5000,
        ...config,
        type: 'error'
      })
    }
  }

  const showWarning = (config: string | NotificationConfig) => {
    if (typeof config === 'string') {
      ElNotification.warning({
        title: '警告',
        message: config,
        duration: 4000
      })
    } else {
      ElNotification.warning({
        duration: 4000,
        ...config,
        type: 'warning'
      })
    }
  }

  const showInfo = (config: string | NotificationConfig) => {
    if (typeof config === 'string') {
      ElNotification.info({
        title: '提示',
        message: config,
        duration: 3000
      })
    } else {
      ElNotification.info({
        duration: 3000,
        ...config,
        type: 'info'
      })
    }
  }

  const confirm = async (
    message: string,
    title = '确认',
    options: any = {}
  ): Promise<boolean> => {
    try {
      await ElMessageBox.confirm(message, title, {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
        ...options
      })
      return true
    } catch {
      return false
    }
  }

  const prompt = async (
    message: string,
    title = '输入',
    options: any = {}
  ): Promise<string | null> => {
    try {
      const { value } = await ElMessageBox.prompt(message, title, {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        ...options
      })
      return value
    } catch {
      return null
    }
  }

  return {
    showSuccess,
    showError,
    showWarning,
    showInfo,
    confirm,
    prompt
  }
}

// 用户引导
export function useUserGuide() {
  const currentStep = ref(0)
  const isActive = ref(false)
  const steps = ref<GuideStep[]>([])

  const startGuide = (guideSteps: GuideStep[]) => {
    steps.value = guideSteps
    currentStep.value = 0
    isActive.value = true
    showCurrentStep()
  }

  const nextStep = () => {
    const current = steps.value[currentStep.value]
    if (current.onNext) {
      current.onNext()
    }

    if (currentStep.value < steps.value.length - 1) {
      currentStep.value++
      showCurrentStep()
    } else {
      endGuide()
    }
  }

  const prevStep = () => {
    const current = steps.value[currentStep.value]
    if (current.onPrev) {
      current.onPrev()
    }

    if (currentStep.value > 0) {
      currentStep.value--
      showCurrentStep()
    }
  }

  const skipGuide = () => {
    endGuide()
  }

  const endGuide = () => {
    isActive.value = false
    currentStep.value = 0
    steps.value = []
    removeHighlight()
  }

  const showCurrentStep = () => {
    const step = steps.value[currentStep.value]
    if (!step) return

    // 移除之前的高亮
    removeHighlight()

    // 高亮当前目标元素
    nextTick(() => {
      const targetElement = document.querySelector(step.target)
      if (targetElement) {
        highlightElement(targetElement as HTMLElement)
        scrollToElement(targetElement as HTMLElement)
      }
    })
  }

  const highlightElement = (element: HTMLElement) => {
    element.classList.add('guide-highlight')
    element.style.position = 'relative'
    element.style.zIndex = '9999'
  }

  const removeHighlight = () => {
    const highlightedElements = document.querySelectorAll('.guide-highlight')
    highlightedElements.forEach(el => {
      el.classList.remove('guide-highlight')
      ;(el as HTMLElement).style.position = ''
      ;(el as HTMLElement).style.zIndex = ''
    })
  }

  const scrollToElement = (element: HTMLElement) => {
    element.scrollIntoView({
      behavior: 'smooth',
      block: 'center'
    })
  }

  return {
    currentStep: readonly(currentStep),
    isActive: readonly(isActive),
    currentStepData: computed(() => steps.value[currentStep.value]),
    totalSteps: computed(() => steps.value.length),
    startGuide,
    nextStep,
    prevStep,
    skipGuide,
    endGuide
  }
}

// 无障碍功能
export function useAccessibility() {
  const announcements = ref<string[]>([])
  const focusHistory = ref<HTMLElement[]>([])

  // 屏幕阅读器公告
  const announce = (message: string, priority: 'polite' | 'assertive' = 'polite') => {
    announcements.value.push(message)

    // 创建临时的 aria-live 区域
    const liveRegion = document.createElement('div')
    liveRegion.setAttribute('aria-live', priority)
    liveRegion.setAttribute('aria-atomic', 'true')
    liveRegion.style.position = 'absolute'
    liveRegion.style.left = '-10000px'
    liveRegion.style.width = '1px'
    liveRegion.style.height = '1px'
    liveRegion.style.overflow = 'hidden'

    document.body.appendChild(liveRegion)

    // 延迟添加内容以确保屏幕阅读器能够检测到
    setTimeout(() => {
      liveRegion.textContent = message
    }, 100)

    // 清理
    setTimeout(() => {
      document.body.removeChild(liveRegion)
    }, 1000)
  }

  // 焦点管理
  const saveFocus = () => {
    const activeElement = document.activeElement as HTMLElement
    if (activeElement && activeElement !== document.body) {
      focusHistory.value.push(activeElement)
    }
  }

  const restoreFocus = () => {
    const lastFocused = focusHistory.value.pop()
    if (lastFocused && document.contains(lastFocused)) {
      lastFocused.focus()
    }
  }

  const trapFocus = (container: HTMLElement) => {
    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    )
    const firstElement = focusableElements[0] as HTMLElement
    const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement

    const handleTabKey = (event: KeyboardEvent) => {
      if (event.key !== 'Tab') return

      if (event.shiftKey) {
        if (document.activeElement === firstElement) {
          event.preventDefault()
          lastElement.focus()
        }
      } else {
        if (document.activeElement === lastElement) {
          event.preventDefault()
          firstElement.focus()
        }
      }
    }

    container.addEventListener('keydown', handleTabKey)

    // 返回清理函数
    return () => {
      container.removeEventListener('keydown', handleTabKey)
    }
  }

  // 键盘导航
  const handleArrowNavigation = (
    container: HTMLElement,
    orientation: 'horizontal' | 'vertical' = 'vertical'
  ) => {
    const items = container.querySelectorAll('[role="menuitem"], [role="option"], button')
    let currentIndex = 0

    const handleKeyDown = (event: KeyboardEvent) => {
      const { key } = event
      const isHorizontal = orientation === 'horizontal'

      const nextKey = isHorizontal ? 'ArrowRight' : 'ArrowDown'
      const prevKey = isHorizontal ? 'ArrowLeft' : 'ArrowUp'

      if (key === nextKey) {
        event.preventDefault()
        currentIndex = (currentIndex + 1) % items.length
        ;(items[currentIndex] as HTMLElement).focus()
      } else if (key === prevKey) {
        event.preventDefault()
        currentIndex = currentIndex === 0 ? items.length - 1 : currentIndex - 1
        ;(items[currentIndex] as HTMLElement).focus()
      } else if (key === 'Home') {
        event.preventDefault()
        currentIndex = 0
        ;(items[currentIndex] as HTMLElement).focus()
      } else if (key === 'End') {
        event.preventDefault()
        currentIndex = items.length - 1
        ;(items[currentIndex] as HTMLElement).focus()
      }
    }

    container.addEventListener('keydown', handleKeyDown)

    return () => {
      container.removeEventListener('keydown', handleKeyDown)
    }
  }

  return {
    announcements: readonly(announcements),
    announce,
    saveFocus,
    restoreFocus,
    trapFocus,
    handleArrowNavigation
  }
}

// 响应式设计辅助
export function useResponsiveDesign() {
  const screenSize = ref('desktop')
  const isMobile = computed(() => screenSize.value === 'mobile')
  const isTablet = computed(() => screenSize.value === 'tablet')
  const isDesktop = computed(() => screenSize.value === 'desktop')

  const updateScreenSize = () => {
    const width = window.innerWidth
    if (width < 768) {
      screenSize.value = 'mobile'
    } else if (width < 1024) {
      screenSize.value = 'tablet'
    } else {
      screenSize.value = 'desktop'
    }
  }

  onMounted(() => {
    updateScreenSize()
    window.addEventListener('resize', updateScreenSize)
  })

  onUnmounted(() => {
    window.removeEventListener('resize', updateScreenSize)
  })

  return {
    screenSize: readonly(screenSize),
    isMobile,
    isTablet,
    isDesktop
  }
}

// 主题切换
export function useThemeToggle() {
  const currentTheme = ref<'light' | 'dark'>('light')

  const toggleTheme = () => {
    currentTheme.value = currentTheme.value === 'light' ? 'dark' : 'light'
    applyTheme()
  }

  const setTheme = (theme: 'light' | 'dark') => {
    currentTheme.value = theme
    applyTheme()
  }

  const applyTheme = () => {
    document.documentElement.setAttribute('data-theme', currentTheme.value)
    localStorage.setItem('theme', currentTheme.value)
  }

  const initTheme = () => {
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches

    if (savedTheme) {
      currentTheme.value = savedTheme
    } else if (prefersDark) {
      currentTheme.value = 'dark'
    }

    applyTheme()
  }

  onMounted(() => {
    initTheme()
  })

  return {
    currentTheme: readonly(currentTheme),
    isDark: computed(() => currentTheme.value === 'dark'),
    toggleTheme,
    setTheme
  }
}

// 页面标题管理
export function usePageTitle() {
  const baseTitle = '量化交易平台'
  const currentTitle = ref(baseTitle)

  const setTitle = (title: string) => {
    currentTitle.value = title ? `${title} - ${baseTitle}` : baseTitle
    document.title = currentTitle.value
  }

  const resetTitle = () => {
    currentTitle.value = baseTitle
    document.title = baseTitle
  }

  return {
    currentTitle: readonly(currentTitle),
    setTitle,
    resetTitle
  }
}

// 综合用户体验钩子
export function useUserExperience() {
  const loading = useLoadingState()
  const error = useErrorHandling()
  const notifications = useNotifications()
  const guide = useUserGuide()
  const accessibility = useAccessibility()
  const responsive = useResponsiveDesign()
  const theme = useThemeToggle()
  const pageTitle = usePageTitle()

  // 组合操作：带加载和错误处理的异步操作
  const executeWithUX = async <T>(
    asyncFn: () => Promise<T>,
    options: {
      loadingMessage?: string
      successMessage?: string
      errorMessage?: string
      showProgress?: boolean
    } = {}
  ): Promise<T | null> => {
    const { loadingMessage, successMessage, errorMessage, showProgress } = options

    return loading.withLoading(async () => {
      return error.withErrorHandling(
        async () => {
          const result = await asyncFn()

          if (successMessage) {
            notifications.showSuccess(successMessage)
          }

          return result
        },
        (err) => {
          if (errorMessage) {
            error.setError(errorMessage)
          } else {
            error.handleApiError(err)
          }
        }
      )
    }, loadingMessage)
  }

  return {
    // 子模块
    loading,
    error,
    notifications,
    guide,
    accessibility,
    responsive,
    theme,
    pageTitle,

    // 组合功能
    executeWithUX
  }
}
