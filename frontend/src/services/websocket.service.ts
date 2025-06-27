/**
 * WebSocket 服务
 * 处理实时数据连接和消息管理
 */
import { io, Socket } from 'socket.io-client'
import { ElMessage } from 'element-plus'
import mitt from 'mitt'
import type { Emitter } from 'mitt'
import { useUserStore } from '@/stores/modules/user'

export interface WebSocketConfig {
  url: string
  options?: {
    transports?: string[]
    timeout?: number
    forceNew?: boolean
    autoConnect?: boolean
  }
}

export interface WebSocketEvents {
  connect: void
  disconnect: void
  error: Error
  reconnect: number
  'market-data': any
  'trading-update': any
  'notification': any
  'system-message': any
}

export class WebSocketService {
  private socket: Socket | null = null
  private config: WebSocketConfig
  private eventBus: Emitter<WebSocketEvents>
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectTimer: NodeJS.Timeout | null = null
  private heartbeatTimer: NodeJS.Timeout | null = null
  private isConnecting = false

  constructor(config: WebSocketConfig) {
    this.config = config
    this.eventBus = mitt<WebSocketEvents>()
  }

  /**
   * 连接WebSocket
   */
  async connect(): Promise<void> {
    if (this.isConnecting || this.isConnected()) {
      return
    }

    this.isConnecting = true

    try {
      const authStore = useUserStore()
      
      this.socket = io(this.config.url, {
        transports: ['websocket'],
        timeout: 5000,
        forceNew: true,
        auth: {
          token: authStore.token
        },
        ...this.config.options
      })

      this.setupEventListeners()
      
    } catch (error) {
      this.isConnecting = false
      throw error
    }
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    this.clearTimers()
    
    if (this.socket) {
      this.socket.removeAllListeners()
      this.socket.disconnect()
      this.socket = null
    }
    
    this.reconnectAttempts = 0
    this.isConnecting = false
  }

  /**
   * 检查连接状态
   */
  isConnected(): boolean {
    return this.socket?.connected || false
  }

  /**
   * 发送消息
   */
  emit(event: string, data?: any): void {
    if (this.isConnected() && this.socket) {
      this.socket.emit(event, data)
    } else {
      console.warn('WebSocket not connected, message not sent:', event, data)
    }
  }

  /**
   * 监听事件
   */
  on<K extends keyof WebSocketEvents>(
    event: K,
    handler: (data: WebSocketEvents[K]) => void
  ): void {
    this.eventBus.on(event, handler)
  }

  /**
   * 取消监听事件
   */
  off<K extends keyof WebSocketEvents>(
    event: K,
    handler?: (data: WebSocketEvents[K]) => void
  ): void {
    this.eventBus.off(event, handler)
  }

  /**
   * 订阅行情数据
   */
  subscribeMarketData(symbols: string[]): void {
    this.emit('subscribe-market', { symbols })
  }

  /**
   * 取消订阅行情数据
   */
  unsubscribeMarketData(symbols: string[]): void {
    this.emit('unsubscribe-market', { symbols })
  }

  /**
   * 订阅交易更新
   */
  subscribeTradingUpdates(): void {
    this.emit('subscribe-trading')
  }

  /**
   * 取消订阅交易更新
   */
  unsubscribeTradingUpdates(): void {
    this.emit('unsubscribe-trading')
  }

  /**
   * 设置事件监听器
   */
  private setupEventListeners(): void {
    if (!this.socket) return

    this.socket.on('connect', () => {
      console.log('WebSocket connected')
      this.isConnecting = false
      this.reconnectAttempts = 0
      this.eventBus.emit('connect')
      this.startHeartbeat()
    })

    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason)
      this.eventBus.emit('disconnect')
      this.clearTimers()
      
      if (reason === 'io server disconnect') {
        // 服务器主动断开，不重连
        return
      }
      
      this.attemptReconnect()
    })

    this.socket.on('error', (error) => {
      console.error('WebSocket error:', error)
      this.eventBus.emit('error', error)
      ElMessage.error('连接错误: ' + error.message)
    })

    this.socket.on('reconnect', (attemptNumber) => {
      console.log('WebSocket reconnected after', attemptNumber, 'attempts')
      this.eventBus.emit('reconnect', attemptNumber)
      ElMessage.success('连接已恢复')
    })

    // 业务消息监听
    this.socket.on('market-data', (data) => {
      this.eventBus.emit('market-data', data)
    })

    this.socket.on('trading-update', (data) => {
      this.eventBus.emit('trading-update', data)
    })

    this.socket.on('notification', (data) => {
      this.eventBus.emit('notification', data)
    })

    this.socket.on('system-message', (data) => {
      this.eventBus.emit('system-message', data)
    })

    // 心跳响应
    this.socket.on('pong', () => {
      // 心跳响应正常
    })
  }

  /**
   * 尝试重连
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnect attempts reached')
      ElMessage.error('连接失败，请刷新页面重试')
      return
    }

    this.reconnectAttempts++
    const delay = Math.pow(2, this.reconnectAttempts) * 1000 // 指数退避

    console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${delay}ms`)

    this.reconnectTimer = setTimeout(() => {
      if (!this.isConnected()) {
        this.connect().catch(error => {
          console.error('Reconnect failed:', error)
        })
      }
    }, delay)
  }

  /**
   * 启动心跳
   */
  private startHeartbeat(): void {
    this.heartbeatTimer = setInterval(() => {
      if (this.isConnected()) {
        this.emit('ping')
      }
    }, 30000) // 30秒心跳
  }

  /**
   * 清理定时器
   */
  private clearTimers(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }
}

// 创建全局WebSocket服务实例
export const createWebSocketService = (config: WebSocketConfig): WebSocketService => {
  return new WebSocketService(config)
}

// 默认WebSocket服务
let defaultWebSocketService: WebSocketService | null = null

export const getWebSocketService = (): WebSocketService => {
  if (!defaultWebSocketService) {
    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
    defaultWebSocketService = new WebSocketService({
      url: wsUrl,
      options: {
        transports: ['websocket'],
        timeout: 5000,
        autoConnect: false
      }
    })
  }
  return defaultWebSocketService
}