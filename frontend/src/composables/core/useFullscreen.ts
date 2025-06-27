import { ref, onMounted, onUnmounted } from 'vue'
import type { Ref } from 'vue'

/**
 * 全屏API兼容性接口
 */
interface FullscreenAPI {
  requestFullscreen?: () => Promise<void>
  webkitRequestFullscreen?: () => Promise<void>
  mozRequestFullScreen?: () => Promise<void>
  msRequestFullscreen?: () => Promise<void>
}

interface FullscreenDocument extends Document {
  exitFullscreen?: () => Promise<void>
  webkitExitFullscreen?: () => Promise<void>
  mozCancelFullScreen?: () => Promise<void>
  msExitFullscreen?: () => Promise<void>
  fullscreenElement?: Element | null
  webkitFullscreenElement?: Element | null
  mozFullScreenElement?: Element | null
  msFullscreenElement?: Element | null
}

/**
 * 全屏管理组合函数
 * @param target 目标元素引用 (可选，默认为整个页面)
 * @returns 全屏相关状态和方法
 */
export function useFullscreen(target?: Ref<HTMLElement | null>) {
  const isFullscreen = ref(false)
  const isSupported = ref(false)

  /**
   * 检查浏览器是否支持全屏API
   */
  const checkSupport = (): boolean => {
    if (typeof document === 'undefined') return false
    
    const element = document.documentElement as HTMLElement & FullscreenAPI
    
    return !!(
      element.requestFullscreen ||
      element.webkitRequestFullscreen ||
      element.mozRequestFullScreen ||
      element.msRequestFullscreen
    )
  }

  /**
   * 获取当前全屏元素
   */
  const getFullscreenElement = (): Element | null => {
    const doc = document as FullscreenDocument
    
    return (
      doc.fullscreenElement ||
      doc.webkitFullscreenElement ||
      doc.mozFullScreenElement ||
      doc.msFullscreenElement ||
      null
    )
  }

  /**
   * 更新全屏状态
   */
  const updateFullscreenState = () => {
    const fullscreenElement = getFullscreenElement()
    
    if (target?.value) {
      // 如果指定了目标元素，检查该元素是否处于全屏状态
      isFullscreen.value = fullscreenElement === target.value
    } else {
      // 如果没有指定目标元素，检查是否有任何元素处于全屏状态
      isFullscreen.value = !!fullscreenElement
    }
  }

  /**
   * 进入全屏
   */
  const enterFullscreen = async (): Promise<void> => {
    if (!isSupported.value) {
      throw new Error('当前浏览器不支持全屏功能')
    }

    try {
      const element = (target?.value || document.documentElement) as HTMLElement & FullscreenAPI

      if (element.requestFullscreen) {
        await element.requestFullscreen()
      } else if (element.webkitRequestFullscreen) {
        await element.webkitRequestFullscreen()
      } else if (element.mozRequestFullScreen) {
        await element.mozRequestFullScreen()
      } else if (element.msRequestFullscreen) {
        await element.msRequestFullscreen()
      } else {
        throw new Error('无法进入全屏模式')
      }
    } catch (error) {
      console.error('进入全屏失败:', error)
      throw error
    }
  }

  /**
   * 退出全屏
   */
  const exitFullscreen = async (): Promise<void> => {
    if (!isSupported.value) {
      throw new Error('当前浏览器不支持全屏功能')
    }

    try {
      const doc = document as FullscreenDocument

      if (doc.exitFullscreen) {
        await doc.exitFullscreen()
      } else if (doc.webkitExitFullscreen) {
        await doc.webkitExitFullscreen()
      } else if (doc.mozCancelFullScreen) {
        await doc.mozCancelFullScreen()
      } else if (doc.msExitFullscreen) {
        await doc.msExitFullscreen()
      } else {
        throw new Error('无法退出全屏模式')
      }
    } catch (error) {
      console.error('退出全屏失败:', error)
      throw error
    }
  }

  /**
   * 切换全屏状态
   */
  const toggleFullscreen = async (): Promise<void> => {
    if (isFullscreen.value) {
      await exitFullscreen()
    } else {
      await enterFullscreen()
    }
  }

  /**
   * 全屏变化事件处理器
   */
  const handleFullscreenChange = () => {
    updateFullscreenState()
  }

  /**
   * 全屏错误事件处理器
   */
  const handleFullscreenError = (event: Event) => {
    console.error('全屏操作出错:', event)
    updateFullscreenState()
  }

  /**
   * 绑定事件监听器
   */
  const bindEvents = () => {
    if (typeof document === 'undefined') return

    // 全屏变化事件
    document.addEventListener('fullscreenchange', handleFullscreenChange)
    document.addEventListener('webkitfullscreenchange', handleFullscreenChange)
    document.addEventListener('mozfullscreenchange', handleFullscreenChange)
    document.addEventListener('MSFullscreenChange', handleFullscreenChange)

    // 全屏错误事件
    document.addEventListener('fullscreenerror', handleFullscreenError)
    document.addEventListener('webkitfullscreenerror', handleFullscreenError)
    document.addEventListener('mozfullscreenerror', handleFullscreenError)
    document.addEventListener('MSFullscreenError', handleFullscreenError)
  }

  /**
   * 解绑事件监听器
   */
  const unbindEvents = () => {
    if (typeof document === 'undefined') return

    // 全屏变化事件
    document.removeEventListener('fullscreenchange', handleFullscreenChange)
    document.removeEventListener('webkitfullscreenchange', handleFullscreenChange)
    document.removeEventListener('mozfullscreenchange', handleFullscreenChange)
    document.removeEventListener('MSFullscreenChange', handleFullscreenChange)

    // 全屏错误事件
    document.removeEventListener('fullscreenerror', handleFullscreenError)
    document.removeEventListener('webkitfullscreenerror', handleFullscreenError)
    document.removeEventListener('mozfullscreenerror', handleFullscreenError)
    document.removeEventListener('MSFullscreenError', handleFullscreenError)
  }

  // 生命周期钩子
  onMounted(() => {
    isSupported.value = checkSupport()
    updateFullscreenState()
    bindEvents()
  })

  onUnmounted(() => {
    unbindEvents()
  })

  return {
    isFullscreen,
    isSupported,
    enterFullscreen,
    exitFullscreen,
    toggleFullscreen,
    toggle: toggleFullscreen  // 别名
  }
}

/**
 * 简化的全屏切换组合函数
 * @param target 目标元素引用
 * @returns 切换全屏的方法
 */
export function useToggleFullscreen(target?: Ref<HTMLElement | null>) {
  const { toggleFullscreen } = useFullscreen(target)
  return toggleFullscreen
}

/**
 * 检查是否支持全屏API
 */
export function isFullscreenSupported(): boolean {
  if (typeof document === 'undefined') return false
  
  const element = document.documentElement as HTMLElement & FullscreenAPI
  
  return !!(
    element.requestFullscreen ||
    element.webkitRequestFullscreen ||
    element.mozRequestFullScreen ||
    element.msRequestFullscreen
  )
}

/**
 * 获取当前全屏元素 (工具函数)
 */
export function getCurrentFullscreenElement(): Element | null {
  if (typeof document === 'undefined') return null
  
  const doc = document as FullscreenDocument
  
  return (
    doc.fullscreenElement ||
    doc.webkitFullscreenElement ||
    doc.mozFullScreenElement ||
    doc.msFullscreenElement ||
    null
  )
}

/**
 * 检查指定元素是否处于全屏状态
 */
export function isElementFullscreen(element: HTMLElement): boolean {
  const fullscreenElement = getCurrentFullscreenElement()
  return fullscreenElement === element
}

/**
 * 强制退出全屏 (工具函数)
 */
export async function forceExitFullscreen(): Promise<void> {
  if (!isFullscreenSupported()) {
    throw new Error('当前浏览器不支持全屏功能')
  }

  const fullscreenElement = getCurrentFullscreenElement()
  if (!fullscreenElement) {
    return // 已经不在全屏状态
  }

  try {
    const doc = document as FullscreenDocument

    if (doc.exitFullscreen) {
      await doc.exitFullscreen()
    } else if (doc.webkitExitFullscreen) {
      await doc.webkitExitFullscreen()
    } else if (doc.mozCancelFullScreen) {
      await doc.mozCancelFullScreen()
    } else if (doc.msExitFullscreen) {
      await doc.msExitFullscreen()
    } else {
      throw new Error('无法退出全屏模式')
    }
  } catch (error) {
    console.error('强制退出全屏失败:', error)
    throw error
  }
} 