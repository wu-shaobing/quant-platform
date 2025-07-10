/**
 * 应用主入口文件
 * 集成所有必要的插件和配置
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'

import App from './App.vue'
import router from './router'
import { config } from '@/config'
import i18n from '@/locales'
import http from '@/api/http'

// 设置API基础URL
http.defaults.baseURL = config.api.baseURL

// 导入全局样式
// 注意: 按顺序导入, element.scss 依赖 variables.scss, index.scss 依赖 element.scss
import '@/assets/styles/element.scss'
import '@/assets/styles/index.scss'

// 导入Element Plus图标
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

// 导入全局组件
import GlobalComponents from '@/components'

import { setupErrorHandler } from './utils/error-handler'

// 创建Vue应用实例
const app = createApp(App)

// =======================
// Pinia状态管理配置
// =======================
const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)
app.use(pinia)

// =======================
// 路由配置
// =======================
app.use(router)

// =======================
// 国际化配置
// =======================
app.use(i18n)

// =======================
// Element Plus图标注册
// =======================
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// =======================
// 全局组件注册
// =======================
app.use(GlobalComponents)

// =======================
// 错误处理系统初始化
// =======================
setupErrorHandler(app)

// =======================
// 全局属性配置
// =======================
app.config.globalProperties.$config = config

// =======================
// 全局错误处理
// =======================
app.config.errorHandler = (err: unknown, instance, info) => {
  console.error('🚨 全局错误捕获:', {
    error: err,
    errorInfo: info,
    instance: instance?.$options?.name || 'Unknown Component',
    timestamp: new Date().toISOString()
  })

  // 开发环境显示详细错误
  if (config.app.isDev) {
    console.error('错误堆栈:', (err as Error).stack)
  }

  // 生产环境发送错误到监控服务
  if (config.app.isProd) {
    // 集成Sentry或其他错误监控
    reportError(err as Error, {
      component: instance?.$options?.name,
      errorInfo: info,
      userAgent: navigator.userAgent,
      url: window.location.href
    })
  }
}

// =======================
// 未捕获的Promise异常处理
// =======================
window.addEventListener('unhandledrejection', (event) => {
  console.error('🚨 未处理的Promise异常:', event.reason)
  
  if (config.app.isProd) {
    reportError(new Error(event.reason), {
      type: 'unhandledrejection',
      url: window.location.href
    })
  }
  
  // 阻止默认的控制台错误输出
  event.preventDefault()
})

// =======================
// 全局异常处理
// =======================
window.addEventListener('error', (event) => {
  console.error('🚨 全局异常:', {
    message: event.message,
    filename: event.filename,
    lineno: event.lineno,
    colno: event.colno,
    error: event.error
  })

  if (config.app.isProd) {
    reportError(event.error || new Error(event.message), {
      type: 'javascript',
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno
    })
  }
})

// =======================
// 资源加载错误处理
// =======================
window.addEventListener('error', (event: ErrorEvent) => {
  const target = event.target as HTMLElement
  if (target && target !== window) {
    console.error('🚨 资源加载失败:', {
      tagName: target.tagName,
      source: (target as HTMLImageElement | HTMLScriptElement | HTMLLinkElement).src || (target as HTMLLinkElement).href,
      message: event.message
    })

    if (config.app.isProd) {
      reportError(new Error(`资源加载失败: ${target.tagName}`), {
        type: 'resource',
        source: (target as HTMLImageElement | HTMLScriptElement | HTMLLinkElement).src || (target as HTMLLinkElement).href,
        tagName: target.tagName
      })
    }
  }
}, true)

// =======================
// 网络状态监听
// =======================
window.addEventListener('online', () => {
  console.log('🌐 网络连接已恢复')
  // 可以在这里重新初始化WebSocket连接等
})

window.addEventListener('offline', () => {
  console.log('🚫 网络连接已断开')
  // 可以在这里显示离线提示
})

// =======================
// 页面可见性监听
// =======================
document.addEventListener('visibilitychange', () => {
  if (document.hidden) {
    console.log('📱 页面已隐藏')
    // 可以在这里暂停不必要的请求和动画
  } else {
    console.log('👀 页面已显示')
    // 可以在这里恢复数据更新
  }
})

// =======================
// 应用生命周期钩子
// =======================
app.config.warnHandler = (msg, instance, trace) => {
  // 自定义警告处理
  if (config.app.isDev) {
    console.warn('⚠️ Vue警告:', msg)
    console.warn('组件追踪:', trace)
  }
}

// =======================
// 性能监控
// =======================
if (config.app.isProd && 'performance' in window) {
  window.addEventListener('load', () => {
    // 页面加载性能监控
    setTimeout(() => {
      const perfData = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
      
      if (perfData) {
        const loadTime = perfData.loadEventEnd - perfData.navigationStart
        const domContentLoadedTime = perfData.domContentLoadedEventEnd - perfData.navigationStart
        const firstPaintTime = performance.getEntriesByType('paint').find(entry => entry.name === 'first-paint')?.startTime || 0
        
        console.log('📊 页面性能指标:', {
          页面加载时间: `${loadTime}ms`,
          DOM加载时间: `${domContentLoadedTime}ms`,
          首次绘制时间: `${firstPaintTime}ms`
        })

        // 性能数据上报
        reportPerformance({
          loadTime,
          domContentLoadedTime,
          firstPaintTime,
          url: window.location.href
        })
      }
    }, 0)
  })
}

// =======================
// 辅助函数
// =======================

/**
 * 错误上报函数
 */
function reportError(error: Error, context: Record<string, unknown> = {}) {
  // 这里可以集成Sentry、LogRocket等错误监控服务
  try {
    // 模拟发送错误报告
    const errorReport = {
      message: error.message,
      stack: error.stack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      userId: localStorage.getItem(config.auth.tokenKey) ? 'logged_in' : 'anonymous',
      ...context
    }

    // 发送到错误监控服务
    // Sentry.captureException(error, { contexts: { custom: context } })
    
    console.log('📤 错误报告已发送:', errorReport)
  } catch (reportingError) {
    console.error('❌ 错误报告发送失败:', reportingError)
  }
}

/**
 * 性能数据上报函数
 */
function reportPerformance(perfData: Record<string, unknown>) {
  try {
    // 发送性能数据到分析服务
    console.log('📊 性能数据已记录:', perfData)
    
    // 实际项目中可以发送到Analytics服务
    // gtag('event', 'timing_complete', perfData)
  } catch (error) {
    console.error('❌ 性能数据上报失败:', error)
  }
}

// =======================
// 开发环境调试工具
// =======================
if (config.app.isDev) {
  // 暴露一些调试工具到全局
  (window as Record<string, unknown>).__APP_DEBUG__ = {
    app,
    router,
    pinia,
    config,
    version: config.app.version
  }
  
  console.log('🛠️ 开发调试工具已启用，可通过 window.__APP_DEBUG__ 访问')
  console.log(`📱 应用版本: ${config.app.version}`)
  console.log(`🌐 API地址: ${config.api.baseURL}`)
  console.log(`🔌 WebSocket地址: ${config.api.websocket.url}`)
}

// =======================
// PWA支持
// =======================
if (config.app.enablePWA && 'serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then((registration) => {
        console.log('✅ Service Worker 注册成功:', registration.scope)
      })
      .catch((error) => {
        console.error('❌ Service Worker 注册失败:', error)
      })
  })
}

// =======================
// 应用启动
// =======================
app.mount('#app')

console.log(`🚀 ${config.app.name} v${config.app.version} 启动成功!`)
console.log(`🌍 运行环境: ${config.app.isDev ? '开发' : '生产'}`)
console.log(`⏰ 启动时间: ${new Date().toLocaleString('zh-CN')}`)

export default app
