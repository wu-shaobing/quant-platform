/**
 * 统一错误处理系统
 */

import { ElMessage, ElNotification } from 'element-plus'
import type { AxiosError } from 'axios'

// 错误类型枚举
export enum ErrorType {
  NETWORK = 'NETWORK',
  VALIDATION = 'VALIDATION',
  AUTHENTICATION = 'AUTHENTICATION',
  AUTHORIZATION = 'AUTHORIZATION',
  BUSINESS = 'BUSINESS',
  SYSTEM = 'SYSTEM',
  TIMEOUT = 'TIMEOUT',
  UNKNOWN = 'UNKNOWN'
}

// 错误级别枚举
export enum ErrorLevel {
  INFO = 'info',
  WARNING = 'warning',
  ERROR = 'error',
  CRITICAL = 'critical'
}

// 错误信息接口
export interface ErrorInfo {
  type: ErrorType
  level: ErrorLevel
  code: string | number
  message: string
  details?: any
  timestamp: number
  stack?: string
  context?: Record<string, any>
}

// 错误处理选项
export interface ErrorHandlerOptions {
  showNotification?: boolean
  showMessage?: boolean
  logToConsole?: boolean
  logToServer?: boolean
  context?: Record<string, any>
}

// 错误消息映射
const ERROR_MESSAGES: Record<string, string> = {
  // 网络错误
  'NETWORK_ERROR': '网络连接异常，请检查网络设置',
  'TIMEOUT_ERROR': '请求超时，请稍后重试',
  'CONNECTION_REFUSED': '连接被拒绝，请检查服务器状态',
  
  // 认证错误
  'UNAUTHORIZED': '登录已过期，请重新登录',
  'FORBIDDEN': '权限不足，无法访问该资源',
  'TOKEN_EXPIRED': '登录令牌已过期，请重新登录',
  'INVALID_TOKEN': '登录令牌无效，请重新登录',
  
  // 业务错误
  'INVALID_STOCK_CODE': '股票代码格式不正确',
  'INSUFFICIENT_BALANCE': '账户余额不足',
  'MARKET_CLOSED': '市场已关闭，无法进行交易',
  'ORDER_FAILED': '下单失败，请检查订单信息',
  'STRATEGY_NOT_FOUND': '策略不存在',
  'BACKTEST_FAILED': '回测失败，请检查参数设置',
  
  // 系统错误
  'INTERNAL_SERVER_ERROR': '服务器内部错误，请稍后重试',
  'SERVICE_UNAVAILABLE': '服务暂时不可用，请稍后重试',
  'DATABASE_ERROR': '数据库访问异常',
  
  // 验证错误
  'VALIDATION_ERROR': '数据验证失败',
  'REQUIRED_FIELD_MISSING': '必填字段缺失',
  'INVALID_FORMAT': '数据格式不正确',
  
  // 默认错误
  'UNKNOWN_ERROR': '未知错误，请联系技术支持'
}

/**
 * 错误处理器类
 */
export class ErrorHandler {
  private static errorLog: ErrorInfo[] = []
  private static maxLogSize = 1000

  /**
   * 处理错误
   */
  static handle(
    error: Error | AxiosError | any,
    options: ErrorHandlerOptions = {}
  ): ErrorInfo {
    const errorInfo = this.parseError(error, options.context)
    
    // 记录错误日志
    this.logError(errorInfo, options)
    
    // 显示用户提示
    this.showUserNotification(errorInfo, options)
    
    return errorInfo
  }

  /**
   * 解析错误信息
   */
  private static parseError(error: any, context?: Record<string, any>): ErrorInfo {
    const timestamp = Date.now()
    let errorInfo: ErrorInfo = {
      type: ErrorType.UNKNOWN,
      level: ErrorLevel.ERROR,
      code: 'UNKNOWN_ERROR',
      message: ERROR_MESSAGES.UNKNOWN_ERROR,
      timestamp,
      context
    }

    if (error?.isAxiosError) {
      // Axios 错误
      const axiosError = error as AxiosError
      errorInfo = this.parseAxiosError(axiosError, context)
    } else if (error instanceof Error) {
      // 标准 JavaScript 错误
      errorInfo = {
        type: ErrorType.SYSTEM,
        level: ErrorLevel.ERROR,
        code: error.name,
        message: error.message,
        stack: error.stack,
        timestamp,
        context
      }
    } else if (typeof error === 'string') {
      // 字符串错误
      errorInfo = {
        type: ErrorType.BUSINESS,
        level: ErrorLevel.WARNING,
        code: 'CUSTOM_ERROR',
        message: error,
        timestamp,
        context
      }
    } else if (error?.code && error?.message) {
      // 自定义错误对象
      errorInfo = {
        type: this.getErrorType(error.code),
        level: this.getErrorLevel(error.code),
        code: error.code,
        message: ERROR_MESSAGES[error.code] || error.message,
        details: error.details,
        timestamp,
        context
      }
    }

    return errorInfo
  }

  /**
   * 解析 Axios 错误
   */
  private static parseAxiosError(error: AxiosError, context?: Record<string, any>): ErrorInfo {
    const { response, request, code } = error
    const timestamp = Date.now()

    if (response) {
      // 服务器响应错误
      const { status, data } = response
      const errorCode = (data as any)?.code || `HTTP_${status}`
      const errorMessage = (data as any)?.message || this.getHttpErrorMessage(status)

      return {
        type: this.getHttpErrorType(status),
        level: this.getHttpErrorLevel(status),
        code: errorCode,
        message: errorMessage,
        details: data,
        timestamp,
        context: {
          ...context,
          url: response.config?.url,
          method: response.config?.method,
          status
        }
      }
    } else if (request) {
      // 请求发送失败
      return {
        type: ErrorType.NETWORK,
        level: ErrorLevel.ERROR,
        code: code || 'NETWORK_ERROR',
        message: ERROR_MESSAGES.NETWORK_ERROR,
        timestamp,
        context
      }
    } else {
      // 请求配置错误
      return {
        type: ErrorType.SYSTEM,
        level: ErrorLevel.ERROR,
        code: 'REQUEST_CONFIG_ERROR',
        message: error.message,
        timestamp,
        context
      }
    }
  }

  /**
   * 获取 HTTP 错误类型
   */
  private static getHttpErrorType(status: number): ErrorType {
    if (status >= 400 && status < 500) {
      if (status === 401) return ErrorType.AUTHENTICATION
      if (status === 403) return ErrorType.AUTHORIZATION
      if (status === 422) return ErrorType.VALIDATION
      return ErrorType.BUSINESS
    }
    if (status >= 500) return ErrorType.SYSTEM
    return ErrorType.UNKNOWN
  }

  /**
   * 获取 HTTP 错误级别
   */
  private static getHttpErrorLevel(status: number): ErrorLevel {
    if (status >= 500) return ErrorLevel.CRITICAL
    if (status >= 400) return ErrorLevel.ERROR
    return ErrorLevel.WARNING
  }

  /**
   * 获取 HTTP 错误消息
   */
  private static getHttpErrorMessage(status: number): string {
    const messages: Record<number, string> = {
      400: '请求参数错误',
      401: '未授权访问',
      403: '禁止访问',
      404: '资源不存在',
      408: '请求超时',
      422: '数据验证失败',
      429: '请求过于频繁',
      500: '服务器内部错误',
      502: '网关错误',
      503: '服务不可用',
      504: '网关超时'
    }
    return messages[status] || `HTTP错误 ${status}`
  }

  /**
   * 根据错误代码获取错误类型
   */
  private static getErrorType(code: string | number): ErrorType {
    const codeStr = String(code).toLowerCase()
    
    if (codeStr.includes('network') || codeStr.includes('connection')) {
      return ErrorType.NETWORK
    }
    if (codeStr.includes('auth') || codeStr.includes('token')) {
      return ErrorType.AUTHENTICATION
    }
    if (codeStr.includes('forbidden') || codeStr.includes('permission')) {
      return ErrorType.AUTHORIZATION
    }
    if (codeStr.includes('validation') || codeStr.includes('format')) {
      return ErrorType.VALIDATION
    }
    if (codeStr.includes('timeout')) {
      return ErrorType.TIMEOUT
    }
    
    return ErrorType.BUSINESS
  }

  /**
   * 根据错误代码获取错误级别
   */
  private static getErrorLevel(code: string | number): ErrorLevel {
    const codeStr = String(code).toLowerCase()
    
    if (codeStr.includes('critical') || codeStr.includes('fatal')) {
      return ErrorLevel.CRITICAL
    }
    if (codeStr.includes('warning') || codeStr.includes('warn')) {
      return ErrorLevel.WARNING
    }
    if (codeStr.includes('info')) {
      return ErrorLevel.INFO
    }
    
    return ErrorLevel.ERROR
  }

  /**
   * 记录错误日志
   */
  private static logError(errorInfo: ErrorInfo, options: ErrorHandlerOptions) {
    // 添加到内存日志
    this.errorLog.unshift(errorInfo)
    if (this.errorLog.length > this.maxLogSize) {
      this.errorLog = this.errorLog.slice(0, this.maxLogSize)
    }

    // 控制台日志
    if (options.logToConsole !== false) {
      const logMethod = errorInfo.level === ErrorLevel.CRITICAL ? 'error' : 
                       errorInfo.level === ErrorLevel.ERROR ? 'error' :
                       errorInfo.level === ErrorLevel.WARNING ? 'warn' : 'info'
      
      console[logMethod]('Error:', {
        type: errorInfo.type,
        code: errorInfo.code,
        message: errorInfo.message,
        details: errorInfo.details,
        context: errorInfo.context,
        stack: errorInfo.stack
      })
    }

    // 发送到服务器（可选）
    if (options.logToServer && errorInfo.level === ErrorLevel.CRITICAL) {
      this.sendErrorToServer(errorInfo).catch(err => {
        console.error('Failed to send error to server:', err)
      })
    }
  }

  /**
   * 显示用户通知
   */
  private static showUserNotification(errorInfo: ErrorInfo, options: ErrorHandlerOptions) {
    const { showNotification = true, showMessage = false } = options

    if (showMessage) {
      ElMessage({
        type: errorInfo.level === ErrorLevel.WARNING ? 'warning' : 'error',
        message: errorInfo.message,
        duration: 3000
      })
    }

    if (showNotification && errorInfo.level !== ErrorLevel.INFO) {
      ElNotification({
        type: errorInfo.level === ErrorLevel.WARNING ? 'warning' : 'error',
        title: '系统提示',
        message: errorInfo.message,
        duration: 5000,
        position: 'top-right'
      })
    }
  }

  /**
   * 发送错误到服务器
   */
  private static async sendErrorToServer(errorInfo: ErrorInfo): Promise<void> {
    try {
      // 这里应该调用实际的错误上报API
      console.log('Sending error to server:', errorInfo)
    } catch (error) {
      console.error('Failed to send error to server:', error)
    }
  }

  /**
   * 获取错误日志
   */
  static getErrorLog(limit = 100): ErrorInfo[] {
    return this.errorLog.slice(0, limit)
  }

  /**
   * 清除错误日志
   */
  static clearErrorLog(): void {
    this.errorLog = []
  }

  /**
   * 创建业务错误
   */
  static createBusinessError(code: string, message?: string, details?: any): ErrorInfo {
    return {
      type: ErrorType.BUSINESS,
      level: ErrorLevel.ERROR,
      code,
      message: message || ERROR_MESSAGES[code] || '业务处理失败',
      details,
      timestamp: Date.now()
    }
  }

  /**
   * 创建验证错误
   */
  static createValidationError(message: string, details?: any): ErrorInfo {
    return {
      type: ErrorType.VALIDATION,
      level: ErrorLevel.WARNING,
      code: 'VALIDATION_ERROR',
      message,
      details,
      timestamp: Date.now()
    }
  }
}

/**
 * 错误处理装饰器
 */
export function handleError(options: ErrorHandlerOptions = {}) {
  return function (target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const originalMethod = descriptor.value

    descriptor.value = async function (...args: any[]) {
      try {
        return await originalMethod.apply(this, args)
      } catch (error) {
        const errorInfo = ErrorHandler.handle(error, {
          ...options,
          context: {
            ...options.context,
            method: propertyKey,
            args: args.length > 0 ? args : undefined
          }
        })
        
        // 根据配置决定是否重新抛出错误
        if (options.showNotification !== false || options.showMessage !== false) {
          throw errorInfo
        }
        
        return null
      }
    }

    return descriptor
  }
}

/**
 * 异步操作错误处理包装器
 */
export async function withErrorHandling<T>(
  operation: () => Promise<T>,
  options: ErrorHandlerOptions = {}
): Promise<T | null> {
  try {
    return await operation()
  } catch (error) {
    ErrorHandler.handle(error, options)
    return null
  }
}

/**
 * 重试机制
 */
export async function withRetry<T>(
  operation: () => Promise<T>,
  maxRetries = 3,
  delay = 1000,
  options: ErrorHandlerOptions = {}
): Promise<T | null> {
  let lastError: any
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await operation()
    } catch (error) {
      lastError = error
      
      if (attempt === maxRetries) {
        ErrorHandler.handle(error, {
          ...options,
          context: {
            ...options.context,
            attempt,
            maxRetries
          }
        })
        break
      }
      
      // 等待后重试
      await new Promise(resolve => setTimeout(resolve, delay * attempt))
    }
  }
  
  return null
}

/**
 * 设置全局错误处理器
 * 用于在应用启动时初始化错误处理系统
 */
export function setupErrorHandler(app?: any) {
  // 如果传入了 Vue 应用实例，可以设置全局错误处理
  if (app) {
    app.config.errorHandler = (err: unknown, instance: any, info: string) => {
      ErrorHandler.handle(err as Error, {
        context: {
          component: instance?.$options?.name || 'Unknown Component',
          errorInfo: info,
          timestamp: new Date().toISOString()
        }
      })
    }
  }

  // 设置全局未捕获异常处理
  window.addEventListener('error', (event) => {
    ErrorHandler.handle(event.error || new Error(event.message), {
      context: {
        type: 'javascript',
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno
      }
    })
  })

  // 设置未处理的 Promise 异常处理
  window.addEventListener('unhandledrejection', (event) => {
    ErrorHandler.handle(new Error(event.reason), {
      context: {
        type: 'unhandledrejection',
        url: window.location.href
      }
    })
    event.preventDefault()
  })

  console.log('✅ 全局错误处理器已初始化')
}

export default ErrorHandler