import { ref, reactive } from 'vue'
import { ElMessage, ElNotification, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import type { ApiError } from '@/types/api'

// 错误类型
export enum ErrorType {
  NETWORK = 'NETWORK',
  VALIDATION = 'VALIDATION',
  AUTHORIZATION = 'AUTHORIZATION',
  BUSINESS = 'BUSINESS',
  SYSTEM = 'SYSTEM',
  UNKNOWN = 'UNKNOWN'
}

// 错误级别
export enum ErrorLevel {
  INFO = 'INFO',
  WARNING = 'WARNING',
  ERROR = 'ERROR',
  CRITICAL = 'CRITICAL'
}

// 错误信息接口
export interface ErrorInfo {
  id: string
  type: ErrorType
  level: ErrorLevel
  message: string
  details?: any
  timestamp: number
  stack?: string
  context?: Record<string, any>
}

// 错误处理配置
export interface ErrorHandlerConfig {
  showMessage?: boolean
  showNotification?: boolean
  logToConsole?: boolean
  reportToServer?: boolean
  autoRetry?: boolean
  maxRetries?: number
}

// 默认配置
const defaultConfig: ErrorHandlerConfig = {
  showMessage: true,
  showNotification: false,
  logToConsole: true,
  reportToServer: false,
  autoRetry: false,
  maxRetries: 3
}

// 全局错误状态
const globalErrorState = reactive({
  errors: [] as ErrorInfo[],
  isOnline: navigator.onLine,
  lastError: null as ErrorInfo | null
})

// 错误计数器
const errorCounts = reactive<Record<string, number>>({})

export function useErrorHandler(config: ErrorHandlerConfig = {}) {
  const router = useRouter()
  const finalConfig = { ...defaultConfig, ...config }

  // 生成错误ID
  const generateErrorId = (): string => {
    return `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  // 判断错误类型
  const getErrorType = (error: any): ErrorType => {
    if (!navigator.onLine) {
      return ErrorType.NETWORK
    }

    if (error?.response?.status) {
      const status = error.response.status
      if (status === 401 || status === 403) {
        return ErrorType.AUTHORIZATION
      }
      if (status === 422) {
        return ErrorType.VALIDATION
      }
      if (status >= 500) {
        return ErrorType.SYSTEM
      }
      if (status >= 400) {
        return ErrorType.BUSINESS
      }
    }

    if (error?.code === 'NETWORK_ERROR' || error?.message?.includes('Network')) {
      return ErrorType.NETWORK
    }

    return ErrorType.UNKNOWN
  }

  // 判断错误级别
  const getErrorLevel = (error: any, type: ErrorType): ErrorLevel => {
    if (type === ErrorType.SYSTEM) {
      return ErrorLevel.CRITICAL
    }
    if (type === ErrorType.AUTHORIZATION) {
      return ErrorLevel.ERROR
    }
    if (type === ErrorType.VALIDATION) {
      return ErrorLevel.WARNING
    }
    if (type === ErrorType.NETWORK) {
      return ErrorLevel.WARNING
    }
    return ErrorLevel.ERROR
  }

  // 格式化错误消息
  const formatErrorMessage = (error: any, type: ErrorType): string => {
    // 自定义错误消息
    if (error?.message) {
      return error.message
    }

    // API错误响应
    if (error?.response?.data?.message) {
      return error.response.data.message
    }

    // 根据错误类型返回默认消息
    switch (type) {
      case ErrorType.NETWORK:
        return '网络连接失败，请检查网络设置'
      case ErrorType.AUTHORIZATION:
        return '没有权限访问该资源'
      case ErrorType.VALIDATION:
        return '数据验证失败'
      case ErrorType.BUSINESS:
        return '业务处理失败'
      case ErrorType.SYSTEM:
        return '系统错误，请稍后重试'
      default:
        return '未知错误'
    }
  }

  // 处理错误
  const handleError = (
    error: any,
    context?: Record<string, any>,
    customConfig?: Partial<ErrorHandlerConfig>
  ): ErrorInfo => {
    const config = { ...finalConfig, ...customConfig }
    const type = getErrorType(error)
    const level = getErrorLevel(error, type)
    const message = formatErrorMessage(error, type)

    const errorInfo: ErrorInfo = {
      id: generateErrorId(),
      type,
      level,
      message,
      details: error?.response?.data || error,
      timestamp: Date.now(),
      stack: error?.stack,
      context
    }

    // 添加到错误列表
    globalErrorState.errors.push(errorInfo)
    globalErrorState.lastError = errorInfo

    // 限制错误列表长度
    if (globalErrorState.errors.length > 100) {
      globalErrorState.errors.splice(0, 50)
    }

    // 错误计数
    const errorKey = `${type}_${error?.response?.status || 'unknown'}`
    errorCounts[errorKey] = (errorCounts[errorKey] || 0) + 1

    // 控制台日志
    if (config.logToConsole) {
      console.group(`🚨 [${level}] ${type} Error`)
      console.error('Message:', message)
      console.error('Details:', errorInfo.details)
      if (context) console.error('Context:', context)
      if (error?.stack) console.error('Stack:', error.stack)
      console.groupEnd()
    }

    // 显示消息提示
    if (config.showMessage) {
      showErrorMessage(errorInfo)
    }

    // 显示通知
    if (config.showNotification) {
      showErrorNotification(errorInfo)
    }

    // 上报到服务器
    if (config.reportToServer) {
      reportErrorToServer(errorInfo)
    }

    // 特殊错误处理
    handleSpecialErrors(errorInfo)

    return errorInfo
  }

  // 显示错误消息
  const showErrorMessage = (errorInfo: ErrorInfo): void => {
    const { level, message } = errorInfo

    switch (level) {
      case ErrorLevel.INFO:
        ElMessage.info(message)
        break
      case ErrorLevel.WARNING:
        ElMessage.warning(message)
        break
      case ErrorLevel.ERROR:
        ElMessage.error(message)
        break
      case ErrorLevel.CRITICAL:
        ElMessage({
          type: 'error',
          message,
          duration: 0, // 不自动关闭
          showClose: true
        })
        break
    }
  }

  // 显示错误通知
  const showErrorNotification = (errorInfo: ErrorInfo): void => {
    const { level, message, details } = errorInfo

    ElNotification({
      title: `${level} Error`,
      message,
      type: level === ErrorLevel.INFO ? 'info' : 
            level === ErrorLevel.WARNING ? 'warning' : 'error',
      duration: level === ErrorLevel.CRITICAL ? 0 : 4500,
      position: 'bottom-right'
    })
  }

  // 上报错误到服务器
  const reportErrorToServer = async (errorInfo: ErrorInfo): Promise<void> => {
    try {
      // 这里实现错误上报逻辑
      await fetch('/api/errors/report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ...errorInfo,
          userAgent: navigator.userAgent,
          url: window.location.href,
          userId: localStorage.getItem('userId') // 如果有用户ID
        })
      })
    } catch (reportError) {
      console.error('错误上报失败:', reportError)
    }
  }

  // 处理特殊错误
  const handleSpecialErrors = (errorInfo: ErrorInfo): void => {
    const { type, details } = errorInfo

    // 401 未授权 - 跳转到登录页
    if (type === ErrorType.AUTHORIZATION && details?.response?.status === 401) {
      ElMessageBox.confirm(
        '您的登录已过期，请重新登录',
        '登录过期',
        {
          confirmButtonText: '重新登录',
          cancelButtonText: '取消',
          type: 'warning'
        }
      ).then(() => {
        router.push('/login')
      }).catch(() => {
        // 用户取消
      })
    }

    // 网络错误 - 显示网络状态
    if (type === ErrorType.NETWORK) {
      globalErrorState.isOnline = false
    }
  }

  // 清除错误
  const clearError = (errorId: string): void => {
    const index = globalErrorState.errors.findIndex(error => error.id === errorId)
    if (index > -1) {
      globalErrorState.errors.splice(index, 1)
    }
  }

  // 清除所有错误
  const clearAllErrors = (): void => {
    globalErrorState.errors = []
    globalErrorState.lastError = null
  }

  // 重试函数
  const retry = async <T>(
    fn: () => Promise<T>,
    maxRetries: number = finalConfig.maxRetries || 3,
    delay: number = 1000
  ): Promise<T> => {
    let lastError: any

    for (let i = 0; i <= maxRetries; i++) {
      try {
        return await fn()
      } catch (error) {
        lastError = error
        
        if (i === maxRetries) {
          break
        }

        // 指数退避延迟
        await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)))
      }
    }

    throw lastError
  }

  // 网络状态监听
  const setupNetworkListeners = (): void => {
    const updateOnlineStatus = () => {
      globalErrorState.isOnline = navigator.onLine
      
      if (navigator.onLine) {
        ElMessage.success('网络连接已恢复')
      } else {
        ElMessage.warning('网络连接已断开')
      }
    }

    window.addEventListener('online', updateOnlineStatus)
    window.addEventListener('offline', updateOnlineStatus)

    // 返回清理函数
    return () => {
      window.removeEventListener('online', updateOnlineStatus)
      window.removeEventListener('offline', updateOnlineStatus)
    }
  }

  // 获取错误统计
  const getErrorStats = () => {
    return {
      total: globalErrorState.errors.length,
      byType: globalErrorState.errors.reduce((acc, error) => {
        acc[error.type] = (acc[error.type] || 0) + 1
        return acc
      }, {} as Record<ErrorType, number>),
      byLevel: globalErrorState.errors.reduce((acc, error) => {
        acc[error.level] = (acc[error.level] || 0) + 1
        return acc
      }, {} as Record<ErrorLevel, number>),
      counts: { ...errorCounts }
    }
  }

  return {
    // 状态
    errors: globalErrorState.errors,
    isOnline: ref(globalErrorState.isOnline),
    lastError: ref(globalErrorState.lastError),

    // 方法
    handleError,
    clearError,
    clearAllErrors,
    retry,
    setupNetworkListeners,
    getErrorStats,

    // 工具函数
    showErrorMessage,
    showErrorNotification,
    getErrorType,
    getErrorLevel,
    formatErrorMessage
  }
} 