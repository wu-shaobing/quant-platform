/**
 * 前端性能优化工具
 * 包含代码分割、懒加载、缓存优化等功能
 */

import { nextTick, ref, computed, watch } from 'vue'

// 性能监控接口
export interface PerformanceMetrics {
  loadTime: number
  renderTime: number
  memoryUsage: number
  bundleSize: number
  resourceCount: number
  errors: string[]
}

// ============ 缓存管理 ============

interface CacheItem<T> {
  data: T
  timestamp: number
  ttl: number
}

class MemoryCache<T = any> {
  private cache = new Map<string, CacheItem<T>>()
  private maxSize: number
  private defaultTTL: number

  constructor(maxSize: number = 100, defaultTTL: number = 5 * 60 * 1000) {
    this.maxSize = maxSize
    this.defaultTTL = defaultTTL
  }

  set(key: string, data: T, ttl?: number): void {
    // 如果缓存已满，删除最旧的项
    if (this.cache.size >= this.maxSize) {
      const oldestKey = this.cache.keys().next().value
      this.cache.delete(oldestKey)
    }

    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl: ttl || this.defaultTTL
    })
  }

  get(key: string): T | null {
    const item = this.cache.get(key)
    if (!item) return null

    // 检查是否过期
    if (Date.now() - item.timestamp > item.ttl) {
      this.cache.delete(key)
      return null
    }

    return item.data
  }

  has(key: string): boolean {
    return this.get(key) !== null
  }

  delete(key: string): boolean {
    return this.cache.delete(key)
  }

  clear(): void {
    this.cache.clear()
  }

  size(): number {
    return this.cache.size
  }

  // 清理过期项
  cleanup(): void {
    const now = Date.now()
    for (const [key, item] of this.cache.entries()) {
      if (now - item.timestamp > item.ttl) {
        this.cache.delete(key)
      }
    }
  }
}

// 全局缓存实例
export const globalCache = new MemoryCache()

// ============ 防抖和节流 ============

/**
 * 防抖函数
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => func(...args), delay)
  }
}

/**
 * 节流函数
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let lastCall = 0
  
  return (...args: Parameters<T>) => {
    const now = Date.now()
    if (now - lastCall >= delay) {
      lastCall = now
      func(...args)
    }
  }
}

/**
 * Vue 3 防抖 Composable
 */
export function useDebounce<T>(value: T, delay: number) {
  const debouncedValue = ref(value)
  
  watch(
    () => value,
    debounce((newValue) => {
      debouncedValue.value = newValue
    }, delay)
  )
  
  return debouncedValue
}

/**
 * Vue 3 节流 Composable
 */
export function useThrottle<T>(value: T, delay: number) {
  const throttledValue = ref(value)
  
  watch(
    () => value,
    throttle((newValue) => {
      throttledValue.value = newValue
    }, delay)
  )
  
  return throttledValue
}

// ============ 懒加载 ============

/**
 * 图片懒加载
 */
export class LazyImageLoader {
  private observer: IntersectionObserver
  private images = new Set<HTMLImageElement>()

  constructor(options: IntersectionObserverInit = {}) {
    this.observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const img = entry.target as HTMLImageElement
          this.loadImage(img)
          this.observer.unobserve(img)
          this.images.delete(img)
        }
      })
    }, {
      rootMargin: '50px',
      ...options
    })
  }

  observe(img: HTMLImageElement): void {
    this.images.add(img)
    this.observer.observe(img)
  }

  unobserve(img: HTMLImageElement): void {
    this.images.delete(img)
    this.observer.unobserve(img)
  }

  private loadImage(img: HTMLImageElement): void {
    const src = img.dataset.src
    if (src) {
      img.src = src
      img.removeAttribute('data-src')
    }
  }

  destroy(): void {
    this.observer.disconnect()
    this.images.clear()
  }
}

// 全局图片懒加载实例
export const lazyImageLoader = new LazyImageLoader()

/**
 * Vue 3 懒加载指令
 */
export const lazyLoadDirective = {
  mounted(el: HTMLImageElement) {
    lazyImageLoader.observe(el)
  },
  unmounted(el: HTMLImageElement) {
    lazyImageLoader.unobserve(el)
  }
}

// ============ 虚拟滚动 ============

export interface VirtualScrollOptions {
  itemHeight: number
  containerHeight: number
  buffer?: number
}

export function useVirtualScroll<T>(
  items: T[],
  options: VirtualScrollOptions
) {
  const { itemHeight, containerHeight, buffer = 5 } = options
  
  const scrollTop = ref(0)
  const visibleCount = Math.ceil(containerHeight / itemHeight)
  
  const startIndex = computed(() => {
    return Math.max(0, Math.floor(scrollTop.value / itemHeight) - buffer)
  })
  
  const endIndex = computed(() => {
    return Math.min(items.length, startIndex.value + visibleCount + buffer * 2)
  })
  
  const visibleItems = computed(() => {
    return items.slice(startIndex.value, endIndex.value).map((item, index) => ({
      item,
      index: startIndex.value + index
    }))
  })
  
  const totalHeight = computed(() => items.length * itemHeight)
  
  const offsetY = computed(() => startIndex.value * itemHeight)
  
  const onScroll = (event: Event) => {
    const target = event.target as HTMLElement
    scrollTop.value = target.scrollTop
  }
  
  return {
    visibleItems,
    totalHeight,
    offsetY,
    onScroll
  }
}

// ============ 资源预加载 ============

/**
 * 预加载图片
 */
export function preloadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => resolve(img)
    img.onerror = reject
    img.src = src
  })
}

/**
 * 预加载多张图片
 */
export async function preloadImages(srcs: string[]): Promise<HTMLImageElement[]> {
  return Promise.all(srcs.map(preloadImage))
}

/**
 * 预加载脚本
 */
export function preloadScript(src: string): Promise<HTMLScriptElement> {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.onload = () => resolve(script)
    script.onerror = reject
    script.src = src
    document.head.appendChild(script)
  })
}

/**
 * 预加载样式
 */
export function preloadStyle(href: string): Promise<HTMLLinkElement> {
  return new Promise((resolve, reject) => {
    const link = document.createElement('link')
    link.rel = 'stylesheet'
    link.onload = () => resolve(link)
    link.onerror = reject
    link.href = href
    document.head.appendChild(link)
  })
}

// ============ 批量操作 ============

/**
 * 批量执行任务
 */
export async function batchExecute<T, R>(
  items: T[],
  processor: (item: T) => Promise<R>,
  batchSize: number = 10,
  delay: number = 0
): Promise<R[]> {
  const results: R[] = []
  
  for (let i = 0; i < items.length; i += batchSize) {
    const batch = items.slice(i, i + batchSize)
    const batchResults = await Promise.all(batch.map(processor))
    results.push(...batchResults)
    
    // 延迟执行下一批
    if (delay > 0 && i + batchSize < items.length) {
      await new Promise(resolve => setTimeout(resolve, delay))
    }
  }
  
  return results
}

/**
 * 批量DOM更新
 */
export function batchDOMUpdates(updates: (() => void)[]): Promise<void> {
  return new Promise((resolve) => {
    updates.forEach(update => update())
    nextTick(() => resolve())
  })
}

// ============ 内存管理 ============

/**
 * 内存使用监控
 */
export function getMemoryUsage(): MemoryInfo | null {
  if ('memory' in performance) {
    return (performance as any).memory
  }
  return null
}

/**
 * 清理函数管理器
 */
export class CleanupManager {
  private cleanupFunctions: (() => void)[] = []

  add(cleanup: () => void): void {
    this.cleanupFunctions.push(cleanup)
  }

  cleanup(): void {
    this.cleanupFunctions.forEach(fn => {
      try {
        fn()
      } catch (error) {
        console.error('Cleanup error:', error)
      }
    })
    this.cleanupFunctions = []
  }
}

// ============ 性能监控 ============

/**
 * 性能计时器
 */
export class PerformanceTimer {
  private marks = new Map<string, number>()
  private measures = new Map<string, number>()

  mark(name: string): void {
    this.marks.set(name, performance.now())
  }

  measure(name: string, startMark?: string, endMark?: string): number {
    const endTime = endMark ? this.marks.get(endMark) || performance.now() : performance.now()
    const startTime = startMark ? this.marks.get(startMark) || 0 : 0
    const duration = endTime - startTime
    
    this.measures.set(name, duration)
    return duration
  }

  getMeasure(name: string): number | undefined {
    return this.measures.get(name)
  }

  getAllMeasures(): Record<string, number> {
    return Object.fromEntries(this.measures)
  }

  clear(): void {
    this.marks.clear()
    this.measures.clear()
  }
}

// 全局性能计时器
export const performanceTimer = new PerformanceTimer()

/**
 * 函数执行时间测量
 */
export function measureTime<T extends (...args: any[]) => any>(
  func: T,
  name?: string
): T {
  return ((...args: Parameters<T>) => {
    const startTime = performance.now()
    const result = func(...args)
    const endTime = performance.now()
    const duration = endTime - startTime
    
    console.log(`${name || func.name || 'Function'} executed in ${duration.toFixed(2)}ms`)
    
    return result
  }) as T
}

/**
 * 异步函数执行时间测量
 */
export function measureAsyncTime<T extends (...args: any[]) => Promise<any>>(
  func: T,
  name?: string
): T {
  return (async (...args: Parameters<T>) => {
    const startTime = performance.now()
    const result = await func(...args)
    const endTime = performance.now()
    const duration = endTime - startTime
    
    console.log(`${name || func.name || 'Async Function'} executed in ${duration.toFixed(2)}ms`)
    
    return result
  }) as T
}

// ============ 配置 ============

export const PERFORMANCE_CONFIG = {
  cache: {
    maxSize: 100,
    defaultTTL: 5 * 60 * 1000, // 5分钟
    cleanupInterval: 10 * 60 * 1000 // 10分钟
  },
  
  debounce: {
    search: 300,
    resize: 100,
    scroll: 50
  },
  
  throttle: {
    api: 1000,
    animation: 16, // 60fps
    scroll: 100
  },
  
  virtualScroll: {
    buffer: 5,
    itemHeight: 50
  },
  
  batch: {
    size: 10,
    delay: 100
  }
}

// 自动清理过期缓存
setInterval(() => {
  globalCache.cleanup()
}, PERFORMANCE_CONFIG.cache.cleanupInterval)
