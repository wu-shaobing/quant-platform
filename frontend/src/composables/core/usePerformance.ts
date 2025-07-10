/**
 * 性能监控和优化组合函数
 */

import { ref, computed, watchEffect, onMounted, onUnmounted, type Ref } from 'vue'
import { debounce, throttle } from 'lodash-es'

interface PerformanceMetrics {
  renderTime: number
  memoryUsage: number
  fps: number
  componentCount: number
  apiResponseTime: number
}

interface UsePerformanceOptions {
  enableFPSMonitoring?: boolean
  enableMemoryMonitoring?: boolean
  enableRenderTracking?: boolean
  reportInterval?: number
}

/**
 * 性能监控Hook
 */
export function usePerformance(options: UsePerformanceOptions = {}) {
  const {
    enableFPSMonitoring = false,
    enableMemoryMonitoring = false,
    enableRenderTracking = false,
    reportInterval = 5000
  } = options

  const metrics = ref<PerformanceMetrics>({
    renderTime: 0,
    memoryUsage: 0,
    fps: 0,
    componentCount: 0,
    apiResponseTime: 0
  })

  const isMonitoring = ref(false)
  let performanceObserver: PerformanceObserver | null = null
  let fpsCounter: number | null = null
  let reportTimer: NodeJS.Timeout | null = null

  // FPS监控
  const startFPSMonitoring = () => {
    if (!enableFPSMonitoring) return

    let frames = 0
    let lastTime = performance.now()

    const countFrame = () => {
      frames++
      const currentTime = performance.now()
      
      if (currentTime - lastTime >= 1000) {
        metrics.value.fps = Math.round(frames * 1000 / (currentTime - lastTime))
        frames = 0
        lastTime = currentTime
      }
      
      fpsCounter = requestAnimationFrame(countFrame)
    }

    fpsCounter = requestAnimationFrame(countFrame)
  }

  const stopFPSMonitoring = () => {
    if (fpsCounter) {
      cancelAnimationFrame(fpsCounter)
      fpsCounter = null
    }
  }

  // 内存监控
  const getMemoryUsage = () => {
    if (!enableMemoryMonitoring || !(window as any).performance?.memory) return 0

    const memory = (window as any).performance.memory
    return Math.round(memory.usedJSHeapSize / 1024 / 1024) // MB
  }

  // 渲染性能监控
  const startRenderTracking = () => {
    if (!enableRenderTracking || !window.PerformanceObserver) return

    try {
      performanceObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries()
        
        entries.forEach((entry) => {
          if (entry.entryType === 'measure') {
            metrics.value.renderTime = entry.duration
          } else if (entry.entryType === 'navigation') {
            const navEntry = entry as PerformanceNavigationTiming
            metrics.value.apiResponseTime = navEntry.responseEnd - navEntry.requestStart
          }
        })
      })

      performanceObserver.observe({ 
        entryTypes: ['measure', 'navigation', 'paint'] 
      })
    } catch (error) {
      console.warn('Performance Observer not supported:', error)
    }
  }

  const stopRenderTracking = () => {
    if (performanceObserver) {
      performanceObserver.disconnect()
      performanceObserver = null
    }
  }

  // 开始监控
  const startMonitoring = () => {
    if (isMonitoring.value) return

    isMonitoring.value = true
    
    startFPSMonitoring()
    startRenderTracking()

    // 定期更新内存使用情况
    reportTimer = setInterval(() => {
      metrics.value.memoryUsage = getMemoryUsage()
    }, reportInterval)
  }

  // 停止监控
  const stopMonitoring = () => {
    if (!isMonitoring.value) return

    isMonitoring.value = false
    
    stopFPSMonitoring()
    stopRenderTracking()

    if (reportTimer) {
      clearInterval(reportTimer)
      reportTimer = null
    }
  }

  // 测量函数执行时间
  const measureFunction = async <T>(fn: () => Promise<T> | T, name?: string): Promise<T> => {
    const markName = name || `function-${Date.now()}`
    const startMark = `${markName}-start`
    const endMark = `${markName}-end`
    const measureName = `${markName}-duration`

    performance.mark(startMark)
    
    try {
      const result = await fn()
      performance.mark(endMark)
      performance.measure(measureName, startMark, endMark)
      
      const measure = performance.getEntriesByName(measureName)[0]
      console.log(`${markName} took ${measure.duration.toFixed(2)}ms`)
      
      return result
    } finally {
      // 清理performance marks
      performance.clearMarks(startMark)
      performance.clearMarks(endMark)
      performance.clearMeasures(measureName)
    }
  }

  // 组件挂载时开始监控
  onMounted(() => {
    startMonitoring()
  })

  // 组件卸载时停止监控
  onUnmounted(() => {
    stopMonitoring()
  })

  return {
    metrics,
    isMonitoring,
    startMonitoring,
    stopMonitoring,
    measureFunction
  }
}

/**
 * 防抖Hook
 */
export function useDebounce<T extends (...args: any[]) => any>(
  fn: T,
  delay = 300
): T {
  return debounce(fn, delay) as T
}

/**
 * 节流Hook
 */
export function useThrottle<T extends (...args: any[]) => any>(
  fn: T,
  delay = 300
): T {
  return throttle(fn, delay) as T
}

/**
 * 虚拟滚动Hook
 */
export function useVirtualScroll<T>(options: {
  items: T[]
  itemHeight: number
  containerHeight: number
  overscan?: number
}) {
  const { items, itemHeight, containerHeight, overscan = 5 } = options
  
  const scrollTop = ref(0)
  const isScrolling = ref(false)
  
  const visibleCount = Math.ceil(containerHeight / itemHeight)
  const startIndex = ref(0)
  const endIndex = ref(visibleCount)
  
  let scrollEndTimer: NodeJS.Timeout
  
  const updateVisibleRange = useThrottle(() => {
    const start = Math.floor(scrollTop.value / itemHeight)
    const end = Math.min(start + visibleCount + overscan, items.length)
    
    startIndex.value = Math.max(0, start - overscan)
    endIndex.value = end
  }, 16) // 60fps
  
  const handleScroll = (event: Event) => {
    const target = event.target as HTMLElement
    scrollTop.value = target.scrollTop
    isScrolling.value = true
    
    updateVisibleRange()
    
    // 滚动结束检测
    clearTimeout(scrollEndTimer)
    scrollEndTimer = setTimeout(() => {
      isScrolling.value = false
    }, 150)
  }
  
  const visibleItems = computed(() => {
    return items.slice(startIndex.value, endIndex.value)
  })
  
  const offsetY = computed(() => startIndex.value * itemHeight)
  const totalHeight = computed(() => items.length * itemHeight)
  
  onUnmounted(() => {
    clearTimeout(scrollEndTimer)
  })
  
  return {
    scrollTop,
    isScrolling,
    visibleItems,
    offsetY,
    totalHeight,
    handleScroll
  }
}

/**
 * 图片懒加载Hook
 */
export function useLazyImage() {
  const imageRef = ref<HTMLImageElement>()
  const isLoaded = ref(false)
  const isError = ref(false)
  const isIntersecting = ref(false)
  
  let observer: IntersectionObserver | null = null
  
  const load = (src: string) => {
    if (!imageRef.value) return
    
    const img = new Image()
    img.onload = () => {
      if (imageRef.value) {
        imageRef.value.src = src
        isLoaded.value = true
      }
    }
    img.onerror = () => {
      isError.value = true
    }
    img.src = src
  }
  
  const startObserving = (src: string) => {
    if (!imageRef.value || !window.IntersectionObserver) {
      load(src)
      return
    }
    
    observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            isIntersecting.value = true
            load(src)
            observer?.disconnect()
          }
        })
      },
      {
        rootMargin: '50px'
      }
    )
    
    observer.observe(imageRef.value)
  }
  
  onUnmounted(() => {
    observer?.disconnect()
  })
  
  return {
    imageRef,
    isLoaded,
    isError,
    isIntersecting,
    startObserving
  }
}

/**
 * 组件缓存Hook
 */
export function useComponentCache<T>(
  factory: () => T,
  deps: () => any[] = () => []
): Ref<T> {
  const cache = new WeakMap()
  const depsRef = ref(deps())
  const cachedValue = ref<T>()
  
  const getCachedValue = () => {
    const currentDeps = deps()
    const depsKey = JSON.stringify(currentDeps)
    
    if (cache.has(depsKey)) {
      return cache.get(depsKey)
    }
    
    const newValue = factory()
    cache.set(depsKey, newValue)
    return newValue
  }
  
  watchEffect(() => {
    cachedValue.value = getCachedValue()
  })
  
  return cachedValue as Ref<T>
}

export default usePerformance