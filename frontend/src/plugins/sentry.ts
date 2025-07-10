import * as Sentry from '@sentry/vue'
import { Router } from 'vue-router'
import type { App } from 'vue'

/**
 * Sentry 错误监控插件
 */
export function setupSentry(app: App, router: Router) {
  const dsn = import.meta.env.VITE_SENTRY_DSN
  const environment = import.meta.env.VITE_SENTRY_ENVIRONMENT || 'development'
  
  // 只在生产环境或配置了DSN时启用Sentry
  if (dsn && environment !== 'development') {
    Sentry.init({
      app,
      dsn,
      environment,
      integrations: [
        new Sentry.BrowserTracing({
          routingInstrumentation: Sentry.vueRouterInstrumentation(router),
        }),
        new Sentry.Replay({
          maskAllText: true,
          blockAllMedia: true,
        }),
      ],
      // 性能监控采样率
      tracesSampleRate: 0.1,
      // 会话重放采样率
      replaysSessionSampleRate: 0.1,
      replaysOnErrorSampleRate: 1.0,
      // 错误过滤
      beforeSend(event, hint) {
        // 过滤掉开发环境的错误
        if (environment === 'development') {
          return null
        }
        
        // 过滤掉网络错误
        if (hint.originalException?.name === 'NetworkError') {
          return null
        }
        
        return event
      },
      // 设置用户上下文
      initialScope: {
        tags: {
          component: 'quant-platform-frontend',
        },
      },
    })

    console.log('Sentry initialized for environment:', environment)
  } else {
    console.log('Sentry not initialized - missing DSN or in development mode')
  }
}

/**
 * 手动捕获错误
 */
export function captureError(error: Error, context?: Record<string, any>) {
  Sentry.withScope((scope) => {
    if (context) {
      scope.setContext('additional_info', context)
    }
    Sentry.captureException(error)
  })
}

/**
 * 设置用户信息
 */
export function setUser(user: { id: string; email?: string; username?: string }) {
  Sentry.setUser(user)
}

/**
 * 添加面包屑
 */
export function addBreadcrumb(message: string, category: string, level: Sentry.SeverityLevel = 'info') {
  Sentry.addBreadcrumb({
    message,
    category,
    level,
    timestamp: Date.now(),
  })
}

/**
 * 性能监控
 */
export function startTransaction(name: string, op: string) {
  return Sentry.startTransaction({ name, op })
}

export default {
  setupSentry,
  captureError,
  setUser,
  addBreadcrumb,
  startTransaction,
}