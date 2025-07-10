import { ref, reactive, computed, nextTick } from 'vue'
import { ElLoading } from 'element-plus'
import type { LoadingInstance } from 'element-plus/es/components/loading/src/loading'

// 加载状态类型
export interface LoadingState {
  id: string
  key: string
  message?: string
  background?: string
  spinner?: string
  customClass?: string
  target?: string | HTMLElement
  fullscreen?: boolean
  lock?: boolean
  timestamp: number
}

// 加载配置
export interface LoadingConfig {
  message?: string
  background?: string
  spinner?: string
  customClass?: string
  target?: string | HTMLElement
  fullscreen?: boolean
  lock?: boolean
  delay?: number
  timeout?: number
}

// 默认配置
const defaultConfig: Required<Omit<LoadingConfig, 'target' | 'delay' | 'timeout'>> = {
  message: '加载中...',
  background: 'rgba(0, 0, 0, 0.7)',
  spinner: '',
  customClass: '',
  fullscreen: false,
  lock: true
}

// 全局加载状态
const globalLoadingState = reactive({
  loadings: new Map<string, LoadingState>(),
  instances: new Map<string, LoadingInstance>(),
  globalLoading: false,
  requestCount: 0
})

// 生成唯一ID
const generateId = (): string => {
  return `loading_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

export function useLoading() {
  // 创建加载状态
  const show = (key: string, config: LoadingConfig = {}): string => {
    const finalConfig = { ...defaultConfig, ...config }
    const id = generateId()

    const loadingState: LoadingState = {
      id,
      key,
      message: finalConfig.message,
      background: finalConfig.background,
      spinner: finalConfig.spinner,
      customClass: finalConfig.customClass,
      target: config.target,
      fullscreen: finalConfig.fullscreen,
      lock: finalConfig.lock,
      timestamp: Date.now()
    }

    // 如果已存在相同key的加载，先隐藏
    if (globalLoadingState.loadings.has(key)) {
      hide(key)
    }

    // 延迟显示
    if (config.delay && config.delay > 0) {
      setTimeout(() => {
        if (globalLoadingState.loadings.has(key)) {
          showLoadingInstance(loadingState)
        }
      }, config.delay)
    } else {
      showLoadingInstance(loadingState)
    }

    // 设置超时自动隐藏
    if (config.timeout && config.timeout > 0) {
      setTimeout(() => {
        hide(key)
      }, config.timeout)
    }

    globalLoadingState.loadings.set(key, loadingState)
    updateGlobalLoading()

    return id
  }

  // 显示加载实例
  const showLoadingInstance = (loadingState: LoadingState): void => {
    try {
      const options: any = {
        text: loadingState.message,
        background: loadingState.background,
        customClass: loadingState.customClass,
        lock: loadingState.lock
      }

      if (loadingState.spinner) {
        options.spinner = loadingState.spinner
      }

      if (loadingState.fullscreen) {
        options.target = document.body
      } else if (loadingState.target) {
        if (typeof loadingState.target === 'string') {
          options.target = document.querySelector(loadingState.target)
        } else {
          options.target = loadingState.target
        }
      }

      const instance = ElLoading.service(options)
      globalLoadingState.instances.set(loadingState.key, instance)
    } catch (error) {
      console.error('创建加载实例失败:', error)
    }
  }

  // 隐藏加载状态
  const hide = (key: string): void => {
    const instance = globalLoadingState.instances.get(key)
    if (instance) {
      try {
        instance.close()
        globalLoadingState.instances.delete(key)
      } catch (error) {
        console.error('关闭加载实例失败:', error)
      }
    }

    globalLoadingState.loadings.delete(key)
    updateGlobalLoading()
  }

  // 通过ID隐藏
  const hideById = (id: string): void => {
    for (const [key, loading] of globalLoadingState.loadings.entries()) {
      if (loading.id === id) {
        hide(key)
        break
      }
    }
  }

  // 隐藏所有加载状态
  const hideAll = (): void => {
    // 关闭所有实例
    globalLoadingState.instances.forEach(instance => {
      try {
        instance.close()
      } catch (error) {
        console.error('关闭加载实例失败:', error)
      }
    })

    globalLoadingState.loadings.clear()
    globalLoadingState.instances.clear()
    updateGlobalLoading()
  }

  // 更新全局加载状态
  const updateGlobalLoading = (): void => {
    globalLoadingState.globalLoading = globalLoadingState.loadings.size > 0
  }

  // 检查是否正在加载
  const isLoading = (key?: string): boolean => {
    if (key) {
      return globalLoadingState.loadings.has(key)
    }
    return globalLoadingState.globalLoading
  }

  // 获取加载状态
  const getLoading = (key: string): LoadingState | undefined => {
    return globalLoadingState.loadings.get(key)
  }

  // 获取所有加载状态
  const getAllLoadings = (): LoadingState[] => {
    return Array.from(globalLoadingState.loadings.values())
  }

  // 异步函数包装器
  const withLoading = async <T>(
    fn: () => Promise<T>,
    key: string,
    config?: LoadingConfig
  ): Promise<T> => {
    show(key, config)
    try {
      const result = await fn()
      return result
    } finally {
      hide(key)
    }
  }

  // 请求计数器相关
  const incrementRequestCount = (): void => {
    globalLoadingState.requestCount++
    if (globalLoadingState.requestCount === 1) {
      show('global-request', {
        message: '请求处理中...',
        fullscreen: true,
        delay: 300 // 300ms后显示，避免闪烁
      })
    }
  }

  const decrementRequestCount = (): void => {
    globalLoadingState.requestCount = Math.max(0, globalLoadingState.requestCount - 1)
    if (globalLoadingState.requestCount === 0) {
      hide('global-request')
    }
  }

  // 页面级加载
  const showPageLoading = (message: string = '页面加载中...'): string => {
    return show('page-loading', {
      message,
      fullscreen: true,
      background: 'rgba(255, 255, 255, 0.9)',
      customClass: 'page-loading'
    })
  }

  const hidePageLoading = (): void => {
    hide('page-loading')
  }

  // 组件级加载
  const showComponentLoading = (
    target: string | HTMLElement,
    message: string = '加载中...'
  ): string => {
    return show(`component-${Date.now()}`, {
      message,
      target,
      lock: true,
      background: 'rgba(255, 255, 255, 0.8)'
    })
  }

  // 表格加载
  const showTableLoading = (tableSelector: string = '.el-table'): string => {
    return show('table-loading', {
      message: '数据加载中...',
      target: tableSelector,
      customClass: 'table-loading',
      background: 'rgba(255, 255, 255, 0.9)'
    })
  }

  const hideTableLoading = (): void => {
    hide('table-loading')
  }

  // 按钮加载状态
  const buttonLoadingStates = reactive<Record<string, boolean>>({})

  const setButtonLoading = (buttonKey: string, loading: boolean): void => {
    buttonLoadingStates[buttonKey] = loading
  }

  const isButtonLoading = (buttonKey: string): boolean => {
    return buttonLoadingStates[buttonKey] || false
  }

  // 计算属性
  const loadingCount = computed(() => globalLoadingState.loadings.size)
  const hasAnyLoading = computed(() => globalLoadingState.globalLoading)
  const requestCount = computed(() => globalLoadingState.requestCount)

  // 清理函数
  const cleanup = (): void => {
    hideAll()
    Object.keys(buttonLoadingStates).forEach(key => {
      delete buttonLoadingStates[key]
    })
  }

  // 获取加载统计信息
  const getLoadingStats = () => {
    const loadings = getAllLoadings()
    return {
      total: loadings.length,
      byKey: loadings.reduce((acc, loading) => {
        acc[loading.key] = (acc[loading.key] || 0) + 1
        return acc
      }, {} as Record<string, number>),
      oldestLoading: loadings.reduce((oldest, current) => {
        return !oldest || current.timestamp < oldest.timestamp ? current : oldest
      }, null as LoadingState | null),
      requestCount: globalLoadingState.requestCount
    }
  }

  return {
    // 基本方法
    show,
    hide,
    hideById,
    hideAll,
    isLoading,
    getLoading,
    getAllLoadings,
    withLoading,

    // 请求计数
    incrementRequestCount,
    decrementRequestCount,

    // 特定场景
    showPageLoading,
    hidePageLoading,
    showComponentLoading,
    showTableLoading,
    hideTableLoading,

    // 按钮状态
    setButtonLoading,
    isButtonLoading,
    buttonLoadingStates,

    // 状态
    loadingCount,
    hasAnyLoading,
    requestCount,

    // 工具
    cleanup,
    getLoadingStats
  }
}

// 全局加载管理器
export const globalLoadingManager = {
  show: (key: string, config?: LoadingConfig) => {
    const { show } = useLoading()
    return show(key, config)
  },
  
  hide: (key: string) => {
    const { hide } = useLoading()
    hide(key)
  },
  
  hideAll: () => {
    const { hideAll } = useLoading()
    hideAll()
  },
  
  isLoading: (key?: string) => {
    const { isLoading } = useLoading()
    return isLoading(key)
  },
  
  withLoading: async <T>(
    fn: () => Promise<T>,
    key: string,
    config?: LoadingConfig
  ): Promise<T> => {
    const { withLoading } = useLoading()
    return withLoading(fn, key, config)
  }
} 