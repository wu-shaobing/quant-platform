import { ref, onUnmounted } from 'vue'
import { createWebSocketService, WebSocketService } from '@/services/websocket.service'

export interface UseWebSocketOptions {
  /** WebSocket URL，默认读取环境变量 */
  url?: string
  /** 是否在开发环境下打印调试日志 */
  debug?: boolean
  /** 是否自动连接，默认 true */
  autoConnect?: boolean
}

export const useWebSocket = (options: UseWebSocketOptions = {}) => {
  const {
    url = import.meta.env.VITE_WS_URL,
    debug = import.meta.env.DEV,
    autoConnect = true
  } = options

  // 单例模式
  let service: WebSocketService | null = null
  // 通过ref暴露给外部，便于响应式追踪
  const socket = ref<WebSocketService | null>(null)

  /**
   * 初始化 WebSocketService
   */
  const initService = () => {
    if (!service) {
      service = createWebSocketService({ url })
    }
    return service
  }

  // 连接状态
  const connected = ref(false)
  const isConnecting = ref(false)

  /** 连接 */
  const connect = async (overrideUrl?: string) => {
    if (overrideUrl && overrideUrl !== url) {
      // 重新创建服务实例
      service = createWebSocketService({ url: overrideUrl })
    }
    const ws = initService()
    socket.value = ws
    if (connected.value || isConnecting.value) return
    try {
      isConnecting.value = true
      await ws.connect()
      connected.value = true
      if (debug) console.log('[WebSocket] connected')
    } catch (err) {
      if (debug) console.error('[WebSocket] connect error', err)
    } finally {
      isConnecting.value = false
    }
  }

  /** 断开连接 */
  const disconnect = () => {
    if (!service) return
    service.disconnect()
    connected.value = false
    if (debug) console.log('[WebSocket] disconnected')
  }

  /** 发送消息 */
  const emit = (event: string, data?: any) => {
    service?.emit(event, data)
  }

  /** 别名 */
  const send = emit

  /** 监听事件 */
  const on = (event: string, handler: (data: any) => void) => {
    service?.on<any>(event as any, handler)
  }

  /** 取消监听 */
  const off = (event: string, handler?: (data: any) => void) => {
    service?.off<any>(event as any, handler)
  }

  /** 订阅频道（业务约定） */
  const subscribe = (channel: string, payload?: any, handler?: (data: any) => void) => {
    emit('subscribe', { channel, ...payload })
    if (handler) on(channel, handler)
  }

  /** 取消订阅 */
  const unsubscribe = (channel: string, payload?: any) => {
    emit('unsubscribe', { channel, ...payload })
    off(channel)
  }

  if (autoConnect) {
    connect().catch(console.error)
  }

  // 组件卸载时自动断开（仅组合式函数上下文）
  onUnmounted(() => {
    disconnect()
  })

  return {
    // 兼容旧命名
    connected,
    isConnected: connected,
    isConnecting,
    socket,
    connect,
    disconnect,
    emit,
    send,
    on,
    off,
    subscribe,
    unsubscribe
  }
}
