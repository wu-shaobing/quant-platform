/**
 * 错误处理服务
 * 统一处理应用中的错误和异常
 */
import { ElMessage, ElNotification } from 'element-plus'
import type { AxiosError } from 'axios'

export interface ErrorInfo {
  message: string
  code?: string | number
  type: 'api' | 'business' | 'system' | 'network' | 'validation'
  details?: any
  timestamp: number
  url?: string
  userId?: string
}

export interface ErrorHandlerOptions {
  showNotification?: boolean
  showMessage?: boolean
  logToConsole?: boolean
  reportToServer?: boolean
  customHandler?: (error: ErrorInfo) => void
}

export class ErrorHandlerService {
  private errorQueue: ErrorInfo[] = []
  private maxQueueSize = 100
  private reportEndpoint = '/api/errors'

  /**
   * 处理API错误
   */
  handleApiError(
    error: AxiosError,
    options: ErrorHandlerOptions = {}
  ): void {
    const errorInfo: ErrorInfo = {
      message: this.extractApiErrorMessage(error),
      code: error.response?.status || error.code,
      type: 'api',
      details: {
        url: error.config?.url,
        method: error.config?.method,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data
      },
      timestamp: Date.now(),
      url: window.location.href
    }

    this.processError(errorInfo, {
      showMessage: true,
      logToConsole: true,
      reportToServer: true,
      ...options
    })
  }

  /**
   * 处理业务错误
   */
  handleBusinessError(
    message: string,
    code?: string | number,
    details?: any,
    options: ErrorHandlerOptions = {}
  ): void {
    const errorInfo: ErrorInfo = {
      message,
      code,
      type: 'business',
      details,
      timestamp: Date.now(),
      url: window.location.href
    }

    this.processError(errorInfo, {
      showMessage: true,
      logToConsole: true,
      ...options
    })
  }

  /**
   * 处理系统错误
   */
  handleSystemError(
    error: Error,
    options: ErrorHandlerOptions = {}
  ): void {
    const errorInfo: ErrorInfo = {
      message: error.message,
      type: 'system',
      details: {
        name: error.name,
        stack: error.stack
      },
      timestamp: Date.now(),
      url: window.location.href
    }

    this.processError(errorInfo, {
      showNotification: true,
      logToConsole: true,
      reportToServer: true,
      ...options
    })
  }

  /**
   * 处理网络错误
   */
  handleNetworkError(
    message: string = '网络连接失败',
    options: ErrorHandlerOptions = {}
  ): void {
    const errorInfo: ErrorInfo = {
      message,
      type: 'network',
      timestamp: Date.now(),
      url: window.location.href
    }

    this.processError(errorInfo, {
      showNotification: true,
      logToConsole: true,
      ...options
    })
  }

  /**
   * 处理表单验证错误
   */
  handleValidationError(
    message: string,
    field?: string,
    options: ErrorHandlerOptions = {}
  ): void {
    const errorInfo: ErrorInfo = {
      message,
      type: 'validation',
      details: { field },
      timestamp: Date.now(),
      url: window.location.href
    }

    this.processError(errorInfo, {
      showMessage: true,
      ...options
    })
  }

  /**
   * 获取错误历史
   */
  getErrorHistory(limit = 50): ErrorInfo[] {
    return this.errorQueue.slice(-limit)
  }

  /**
   * 清空错误历史
   */
  clearErrorHistory(): void {
    this.errorQueue = []
  }

  /**
   * 设置错误上报端点
   */
  setReportEndpoint(endpoint: string): void {
    this.reportEndpoint = endpoint
  }

  /**
   * 处理错误的核心方法
   */
  private processError(
    errorInfo: ErrorInfo,
    options: ErrorHandlerOptions
  ): void {
    // 添加到错误队列
    this.addToQueue(errorInfo)

    // 控制台日志
    if (options.logToConsole) {
      this.logToConsole(errorInfo)
    }

    // 显示消息提示
    if (options.showMessage) {
      this.showMessage(errorInfo)
    }

    // 显示通知
    if (options.showNotification) {
      this.showNotification(errorInfo)
    }

    // 上报到服务器
    if (options.reportToServer) {
      this.reportToServer(errorInfo)
    }

    // 自定义处理
    if (options.customHandler) {
      options.customHandler(errorInfo)
    }
  }

  /**
   * 提取API错误消息
   */
  private extractApiErrorMessage(error: AxiosError): string {
    // 优先使用响应中的错误消息
    if (error.response?.data) {
      const data = error.response.data as any
      if (data.message) return data.message
      if (data.error) return data.error
      if (data.msg) return data.msg
    }

    // 根据状态码返回默认消息
    switch (error.response?.status) {
      case 400:
        return '请求参数错误'
      case 401:
        return '身份验证失败，请重新登录'
      case 403:
        return '没有权限访问该资源'
      case 404:
        return '请求的资源不存在'
      case 408:
        return '请求超时，请稍后重试'
      case 429:
        return '请求过于频繁，请稍后重试'
      case 500:
        return '服务器内部错误'
      case 502:
        return '网关错误'
      case 503:
        return '服务暂时不可用'
      case 504:
        return '网关超时'
      default:
        if (error.code === 'NETWORK_ERROR') {
          return '网络连接失败'
        }
        if (error.code === 'TIMEOUT') {
          return '请求超时'
        }
        return error.message || '未知错误'
    }
  }

  /**
   * 添加到错误队列
   */
  private addToQueue(errorInfo: ErrorInfo): void {
    this.errorQueue.push(errorInfo)

    // 限制队列大小
    if (this.errorQueue.length > this.maxQueueSize) {
      this.errorQueue.shift()
    }
  }

  /**
   * 控制台日志
   */
  private logToConsole(errorInfo: ErrorInfo): void {
    const logMethod = errorInfo.type === 'system' ? 'error' : 'warn'
    console[logMethod]('[ErrorHandler]', {
      type: errorInfo.type,
      message: errorInfo.message,
      code: errorInfo.code,
      details: errorInfo.details,
      timestamp: new Date(errorInfo.timestamp).toISOString()
    })
  }

  /**
   * 显示消息提示
   */
  private showMessage(errorInfo: ErrorInfo): void {
    const type = this.getMessageType(errorInfo.type)
    ElMessage({
      type,
      message: errorInfo.message,
      duration: 4000,
      showClose: true
    })
  }

  /**
   * 显示通知
   */
  private showNotification(errorInfo: ErrorInfo): void {
    const type = this.getMessageType(errorInfo.type)
    ElNotification({
      type,
      title: this.getErrorTitle(errorInfo.type),
      message: errorInfo.message,
      duration: 6000,
      position: 'top-right'
    })
  }

  /**
   * 上报到服务器
   */
  private async reportToServer(errorInfo: ErrorInfo): Promise<void> {
    try {
      // 只上报重要错误
      if (!this.shouldReport(errorInfo)) {
        return
      }

      const reportData = {
        ...errorInfo,
        userAgent: navigator.userAgent,
        url: window.location.href,
        timestamp: errorInfo.timestamp
      }

      // 使用 fetch 避免依赖 axios（可能导致循环依赖）
      await fetch(this.reportEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(reportData)
      })
    } catch (error) {
      // 上报失败不影响用户体验，只在开发环境输出
      if (import.meta.env.DEV) {
        console.warn('Failed to report error:', error)
      }
    }
  }

  /**
   * 判断是否需要上报
   */
  private shouldReport(errorInfo: ErrorInfo): boolean {
    // 系统错误和API错误需要上报
    if (errorInfo.type === 'system' || errorInfo.type === 'api') {
      return true
    }

    // 网络错误根据严重程度决定
    if (errorInfo.type === 'network') {
      return true
    }

    // 业务错误和验证错误通常不需要上报
    return false
  }

  /**
   * 获取消息类型
   */
  private getMessageType(errorType: ErrorInfo['type']): 'error' | 'warning' | 'info' {
    switch (errorType) {
      case 'system':
      case 'network':
        return 'error'
      case 'api':
      case 'business':
        return 'warning'
      case 'validation':
        return 'info'
      default:
        return 'error'
    }
  }

  /**
   * 获取错误标题
   */
  private getErrorTitle(errorType: ErrorInfo['type']): string {
    switch (errorType) {
      case 'system':
        return '系统错误'
      case 'api':
        return 'API错误'
      case 'business':
        return '业务错误'
      case 'network':
        return '网络错误'
      case 'validation':
        return '验证错误'
      default:
        return '错误'
    }
  }
}

// 创建全局错误处理服务实例
export const errorHandler = new ErrorHandlerService()

// 全局错误处理器
window.addEventListener('error', (event) => {
  errorHandler.handleSystemError(event.error)
})

window.addEventListener('unhandledrejection', (event) => {
  errorHandler.handleSystemError(
    new Error(event.reason?.message || 'Unhandled Promise Rejection')
  )
})

// Vue 错误处理器（需要在 main.ts 中配置）
export const vueErrorHandler = (error: Error, instance: any, info: string) => {
  errorHandler.handleSystemError(error, {
    details: { componentInfo: info }
  })
}