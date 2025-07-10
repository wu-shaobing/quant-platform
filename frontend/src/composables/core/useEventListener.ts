import { onMounted, onUnmounted, unref, watch } from 'vue'
import type { Ref } from 'vue'

/**
 * 事件监听器配置选项
 */
interface UseEventListenerOptions extends AddEventListenerOptions {
  /**
   * 是否立即绑定事件 (默认: true)
   */
  immediate?: boolean
  /**
   * 是否在组件卸载时自动清理 (默认: true)
   */
  autoCleanup?: boolean
}

/**
 * 目标元素类型
 */
type EventTarget = Window | Document | HTMLElement | null | undefined

/**
 * 通用事件监听器组合函数
 * @param target 目标元素
 * @param event 事件名称
 * @param handler 事件处理函数
 * @param options 配置选项
 * @returns 清理函数
 */
export function useEventListener<T extends Event = Event>(
  target: EventTarget | Ref<EventTarget>,
  event: string,
  handler: (event: T) => void,
  options: UseEventListenerOptions = {}
): () => void {
  const {
    immediate = true,
    autoCleanup = true,
    ...listenerOptions
  } = options

  let cleanup: (() => void) | null = null

  /**
   * 绑定事件监听器
   */
  const bind = () => {
    const element = unref(target)
    if (!element) return

    element.addEventListener(event, handler as EventListener, listenerOptions)
    
    cleanup = () => {
      element.removeEventListener(event, handler as EventListener, listenerOptions)
      cleanup = null
    }
  }

  /**
   * 解绑事件监听器
   */
  const unbind = () => {
    if (cleanup) {
      cleanup()
    }
  }

  if (immediate) {
    if (typeof target === 'object' && 'value' in target) {
      // 如果target是ref，监听其变化
      watch(
        target,
        (newTarget, oldTarget) => {
          if (oldTarget && cleanup) {
            unbind()
          }
          if (newTarget) {
            bind()
          }
        },
        { immediate: true }
      )
    } else {
      // 直接绑定
      onMounted(bind)
    }
  }

  if (autoCleanup) {
    onUnmounted(unbind)
  }

  return unbind
}

/**
 * 窗口事件监听器
 */
export function useWindowEventListener<T extends Event = Event>(
  event: string,
  handler: (event: T) => void,
  options?: UseEventListenerOptions
) {
  return useEventListener(window, event, handler, options)
}

/**
 * 文档事件监听器
 */
export function useDocumentEventListener<T extends Event = Event>(
  event: string,
  handler: (event: T) => void,
  options?: UseEventListenerOptions
) {
  return useEventListener(document, event, handler, options)
}

/**
 * 键盘事件监听器
 */
export function useKeyboardEventListener(
  key: string | string[],
  handler: (event: KeyboardEvent) => void,
  options: UseEventListenerOptions & {
    /**
     * 事件类型 (默认: 'keydown')
     */
    eventType?: 'keydown' | 'keyup' | 'keypress'
    /**
     * 是否需要按下修饰键
     */
    modifiers?: {
      ctrl?: boolean
      alt?: boolean
      shift?: boolean
      meta?: boolean
    }
    /**
     * 是否阻止默认行为 (默认: false)
     */
    preventDefault?: boolean
    /**
     * 是否阻止事件冒泡 (默认: false)
     */
    stopPropagation?: boolean
  } = {}
) {
  const {
    eventType = 'keydown',
    modifiers = {},
    preventDefault = false,
    stopPropagation = false,
    ...listenerOptions
  } = options

  const keys = Array.isArray(key) ? key : [key]

  const keyHandler = (event: KeyboardEvent) => {
    // 检查按键
    const pressedKey = event.key.toLowerCase()
    const isTargetKey = keys.some(k => k.toLowerCase() === pressedKey)
    
    if (!isTargetKey) return

    // 检查修饰键
    if (modifiers.ctrl !== undefined && event.ctrlKey !== modifiers.ctrl) return
    if (modifiers.alt !== undefined && event.altKey !== modifiers.alt) return
    if (modifiers.shift !== undefined && event.shiftKey !== modifiers.shift) return
    if (modifiers.meta !== undefined && event.metaKey !== modifiers.meta) return

    if (preventDefault) {
      event.preventDefault()
    }
    
    if (stopPropagation) {
      event.stopPropagation()
    }

    handler(event)
  }

  return useDocumentEventListener(eventType, keyHandler, listenerOptions)
}

/**
 * 鼠标事件监听器
 */
export function useMouseEventListener(
  target: EventTarget | Ref<EventTarget>,
  event: 'click' | 'mousedown' | 'mouseup' | 'mousemove' | 'mouseenter' | 'mouseleave',
  handler: (event: MouseEvent) => void,
  options?: UseEventListenerOptions
) {
  return useEventListener(target, event, handler, options)
}

/**
 * 点击外部区域监听器
 */
export function useClickOutside(
  target: Ref<HTMLElement | null>,
  handler: (event: MouseEvent) => void,
  options: UseEventListenerOptions = {}
) {
  const clickHandler = (event: MouseEvent) => {
    const element = unref(target)
    if (!element) return

    if (!element.contains(event.target as Node)) {
      handler(event)
    }
  }

  return useDocumentEventListener('click', clickHandler, options)
}

/**
 * 滚动事件监听器
 */
export function useScrollEventListener(
  target: EventTarget | Ref<EventTarget> = window,
  handler: (event: Event) => void,
  options: UseEventListenerOptions & {
    /**
     * 节流延迟 (毫秒)
     */
    throttle?: number
  } = {}
) {
  const { throttle, ...listenerOptions } = options

  let throttleTimer: NodeJS.Timeout | null = null

  const scrollHandler = (event: Event) => {
    if (throttle) {
      if (throttleTimer) return
      
      throttleTimer = setTimeout(() => {
        handler(event)
        throttleTimer = null
      }, throttle)
    } else {
      handler(event)
    }
  }

  const cleanup = useEventListener(target, 'scroll', scrollHandler, listenerOptions)

  return () => {
    if (throttleTimer) {
      clearTimeout(throttleTimer)
      throttleTimer = null
    }
    cleanup()
  }
}

/**
 * 窗口大小变化监听器
 */
export function useResizeEventListener(
  handler: (event: UIEvent) => void,
  options: UseEventListenerOptions & {
    /**
     * 防抖延迟 (毫秒)
     */
    debounce?: number
  } = {}
) {
  const { debounce, ...listenerOptions } = options

  let debounceTimer: NodeJS.Timeout | null = null

  const resizeHandler = (event: UIEvent) => {
    if (debounce) {
      if (debounceTimer) {
        clearTimeout(debounceTimer)
      }
      
      debounceTimer = setTimeout(() => {
        handler(event)
        debounceTimer = null
      }, debounce)
    } else {
      handler(event)
    }
  }

  const cleanup = useWindowEventListener('resize', resizeHandler, listenerOptions)

  return () => {
    if (debounceTimer) {
      clearTimeout(debounceTimer)
      debounceTimer = null
    }
    cleanup()
  }
}

/**
 * 触摸事件监听器
 */
export function useTouchEventListener(
  target: EventTarget | Ref<EventTarget>,
  event: 'touchstart' | 'touchmove' | 'touchend' | 'touchcancel',
  handler: (event: TouchEvent) => void,
  options?: UseEventListenerOptions
) {
  return useEventListener(target, event, handler, options)
}

/**
 * 拖拽事件监听器
 */
export function useDragEventListener(
  target: Ref<HTMLElement | null>,
  handlers: {
    onDragStart?: (event: DragEvent) => void
    onDrag?: (event: DragEvent) => void
    onDragEnd?: (event: DragEvent) => void
    onDragEnter?: (event: DragEvent) => void
    onDragOver?: (event: DragEvent) => void
    onDragLeave?: (event: DragEvent) => void
    onDrop?: (event: DragEvent) => void
  },
  options?: UseEventListenerOptions
) {
  const cleanupFunctions: (() => void)[] = []

  Object.entries(handlers).forEach(([eventName, handler]) => {
    if (handler) {
      const event = eventName.replace('on', '').toLowerCase()
      const cleanup = useEventListener(target, event, handler, options)
      cleanupFunctions.push(cleanup)
    }
  })

  return () => {
    cleanupFunctions.forEach(cleanup => cleanup())
  }
}

/**
 * 媒体查询监听器
 */
export function useMediaQueryEventListener(
  query: string,
  handler: (matches: boolean) => void,
  options: UseEventListenerOptions = {}
) {
  const { immediate = true, autoCleanup = true } = options

  let mediaQuery: MediaQueryList | null = null
  let cleanup: (() => void) | null = null

  const bind = () => {
    if (typeof window === 'undefined' || !window.matchMedia) return

    mediaQuery = window.matchMedia(query)
    
    const changeHandler = (event: MediaQueryListEvent) => {
      handler(event.matches)
    }

    mediaQuery.addEventListener('change', changeHandler)
    
    if (immediate) {
      handler(mediaQuery.matches)
    }

    cleanup = () => {
      if (mediaQuery) {
        mediaQuery.removeEventListener('change', changeHandler)
        mediaQuery = null
      }
      cleanup = null
    }
  }

  const unbind = () => {
    if (cleanup) {
      cleanup()
    }
  }

  onMounted(bind)

  if (autoCleanup) {
    onUnmounted(unbind)
  }

  return unbind
}

/**
 * 页面可见性变化监听器
 */
export function useVisibilityChangeListener(
  handler: (visible: boolean) => void,
  options?: UseEventListenerOptions
) {
  const visibilityHandler = () => {
    handler(!document.hidden)
  }

  return useDocumentEventListener('visibilitychange', visibilityHandler, options)
}

/**
 * 网络状态变化监听器
 */
export function useNetworkStatusListener(
  handler: (online: boolean) => void,
  options?: UseEventListenerOptions
) {
  const onlineHandler = () => handler(true)
  const offlineHandler = () => handler(false)

  const cleanup1 = useWindowEventListener('online', onlineHandler, options)
  const cleanup2 = useWindowEventListener('offline', offlineHandler, options)

  return () => {
    cleanup1()
    cleanup2()
  }
} 