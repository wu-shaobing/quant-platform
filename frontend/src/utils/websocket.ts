import { ElMessage } from 'element-plus'
import type { WebSocketMessage, SubscriptionRequest } from '@/types/api'

// WebSocket连接状态
export enum WebSocketState {
  CONNECTING = 'CONNECTING',
  CONNECTED = 'CONNECTED',
  DISCONNECTING = 'DISCONNECTING',
  DISCONNECTED = 'DISCONNECTED',
  ERROR = 'ERROR'
}

// WebSocket事件类型
export interface WebSocketEventMap {
  'state-change': WebSocketState
  'message': WebSocketMessage
  'error': Event
  'connected': Event
  'disconnected': Event
  'reconnecting': { attempt: number; maxAttempts: number }
}

// WebSocket配置
export interface WebSocketConfig {
  url: string
  protocols?: string[]
  heartbeatInterval?: number
  reconnectInterval?: number
  maxReconnectAttempts?: number
  timeout?: number
  enableHeartbeat?: boolean
  enableReconnect?: boolean
}

// 默认配置
const defaultConfig: Required<WebSocketConfig> = {
  url: '',
  protocols: [],
  heartbeatInterval: 30000, // 30秒
  reconnectInterval: 5000,  // 5秒
  maxReconnectAttempts: 5,
  timeout: 10000,           // 10秒
  enableHeartbeat: true,
  enableReconnect: true
}

export class WebSocketManager {
  private ws: WebSocket | null = null
  private config: Required<WebSocketConfig>
  private state: WebSocketState = WebSocketState.DISCONNECTED
  private listeners: Map<keyof WebSocketEventMap, Set<Function>> = new Map()
  private subscriptions: Map<string, SubscriptionRequest> = new Map()
  private heartbeatTimer: number | null = null
  private reconnectTimer: number | null = null
  private reconnectAttempts = 0
  private messageQueue: WebSocketMessage[] = []
  private isManualClose = false

  constructor(config: WebSocketConfig) {
    this.config = { ...defaultConfig, ...config }
    this.initEventListeners()
  }

  // 初始化事件监听器映射
  private initEventListeners() {
    const events: Array<keyof WebSocketEventMap> = [
      'state-change', 'message', 'error', 'connected', 'disconnected', 'reconnecting'
    ]
    events.forEach(event => {
      this.listeners.set(event, new Set())
    })
  }

  // 连接WebSocket
  public connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.state === WebSocketState.CONNECTED || this.state === WebSocketState.CONNECTING) {
        resolve()
        return
      }

      this.setState(WebSocketState.CONNECTING)
      this.isManualClose = false

      try {
        this.ws = new WebSocket(this.config.url, this.config.protocols)
        
        // 连接超时处理
        const timeout = setTimeout(() => {
          this.ws?.close()
          reject(new Error('WebSocket连接超时'))
        }, this.config.timeout)

        this.ws.onopen = (event) => {
          clearTimeout(timeout)
          this.setState(WebSocketState.CONNECTED)
          this.reconnectAttempts = 0
          this.startHeartbeat()
          this.processMessageQueue()
          this.emit('connected', event)
          resolve()
        }

        this.ws.onclose = (event) => {
          clearTimeout(timeout)
          this.setState(WebSocketState.DISCONNECTED)
          this.stopHeartbeat()
          this.emit('disconnected', event)
          
          if (!this.isManualClose && this.config.enableReconnect) {
            this.scheduleReconnect()
          }
        }

        this.ws.onerror = (event) => {
          clearTimeout(timeout)
          this.setState(WebSocketState.ERROR)
          this.emit('error', event)
          reject(new Error('WebSocket连接错误'))
        }

        this.ws.onmessage = (event) => {
          this.handleMessage(event)
        }

      } catch (error) {
        this.setState(WebSocketState.ERROR)
        reject(error)
      }
    })
  }

  // 断开连接
  public disconnect(): void {
    this.isManualClose = true
    this.stopHeartbeat()
    this.clearReconnectTimer()
    
    if (this.ws) {
      this.setState(WebSocketState.DISCONNECTING)
      this.ws.close(1000, 'Manual disconnect')
    }
  }

  // 发送消息
  public send(message: WebSocketMessage): void {
    if (this.state === WebSocketState.CONNECTED && this.ws) {
      try {
        this.ws.send(JSON.stringify(message))
      } catch (error) {
        console.error('发送WebSocket消息失败:', error)
        ElMessage.error('发送消息失败')
      }
    } else {
      // 连接未建立时，将消息加入队列
      this.messageQueue.push(message)
      
      if (this.state === WebSocketState.DISCONNECTED) {
        this.connect().catch(error => {
          console.error('自动连接失败:', error)
        })
      }
    }
  }

  // 订阅数据
  public subscribe(request: SubscriptionRequest): void {
    const key = this.generateSubscriptionKey(request)
    this.subscriptions.set(key, request)
    
    const message: WebSocketMessage = {
      type: 'subscribe',
      data: request,
      id: this.generateMessageId()
    }
    
    this.send(message)
  }

  // 取消订阅
  public unsubscribe(request: SubscriptionRequest): void {
    const key = this.generateSubscriptionKey(request)
    this.subscriptions.delete(key)
    
    const message: WebSocketMessage = {
      type: 'unsubscribe',
      data: request,
      id: this.generateMessageId()
    }
    
    this.send(message)
  }

  // 获取所有订阅
  public getSubscriptions(): SubscriptionRequest[] {
    return Array.from(this.subscriptions.values())
  }

  // 清除所有订阅
  public clearSubscriptions(): void {
    this.subscriptions.forEach(subscription => {
      this.unsubscribe(subscription)
    })
    this.subscriptions.clear()
  }

  // 添加事件监听器
  public on<K extends keyof WebSocketEventMap>(
    event: K,
    listener: (data: WebSocketEventMap[K]) => void
  ): void {
    const listeners = this.listeners.get(event)
    if (listeners) {
      listeners.add(listener)
    }
  }

  // 移除事件监听器
  public off<K extends keyof WebSocketEventMap>(
    event: K,
    listener: (data: WebSocketEventMap[K]) => void
  ): void {
    const listeners = this.listeners.get(event)
    if (listeners) {
      listeners.delete(listener)
    }
  }

  // 获取当前状态
  public getState(): WebSocketState {
    return this.state
  }

  // 获取连接状态
  public isConnected(): boolean {
    return this.state === WebSocketState.CONNECTED
  }

  // 处理接收到的消息
  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data)
      
      // 处理心跳响应
      if (message.type === 'pong') {
        return
      }
      
      // 处理订阅确认
      if (message.type === 'subscription_success' || message.type === 'unsubscription_success') {
        console.log('订阅操作成功:', message.data)
        return
      }
      
      // 处理错误消息
      if (message.type === 'error') {
        console.error('WebSocket错误:', message.data)
        ElMessage.error(message.data?.message || 'WebSocket错误')
        return
      }
      
      // 发射消息事件
      this.emit('message', message)
      
    } catch (error) {
      console.error('解析WebSocket消息失败:', error)
    }
  }

  // 设置状态
  private setState(newState: WebSocketState): void {
    if (this.state !== newState) {
      this.state = newState
      this.emit('state-change', newState)
    }
  }

  // 发射事件
  private emit<K extends keyof WebSocketEventMap>(
    event: K,
    data: WebSocketEventMap[K]
  ): void {
    const listeners = this.listeners.get(event)
    if (listeners) {
      listeners.forEach(listener => {
        try {
          listener(data)
        } catch (error) {
          console.error(`WebSocket事件监听器错误 (${event}):`, error)
        }
      })
    }
  }

  // 开始心跳
  private startHeartbeat(): void {
    if (!this.config.enableHeartbeat) return
    
    this.stopHeartbeat()
    this.heartbeatTimer = window.setInterval(() => {
      if (this.isConnected()) {
        this.send({
          type: 'ping',
          data: { timestamp: Date.now() }
        })
      }
    }, this.config.heartbeatInterval)
  }

  // 停止心跳
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  // 安排重连
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
      console.error('WebSocket重连次数已达上限')
      ElMessage.error('连接已断开，请刷新页面重试')
      return
    }

    this.clearReconnectTimer()
    
    this.reconnectAttempts++
    this.emit('reconnecting', {
      attempt: this.reconnectAttempts,
      maxAttempts: this.config.maxReconnectAttempts
    })

    this.reconnectTimer = window.setTimeout(() => {
      console.log(`WebSocket重连尝试 ${this.reconnectAttempts}/${this.config.maxReconnectAttempts}`)
      this.connect().catch(error => {
        console.error('重连失败:', error)
      })
    }, this.config.reconnectInterval * this.reconnectAttempts)
  }

  // 清除重连定时器
  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
  }

  // 处理消息队列
  private processMessageQueue(): void {
    while (this.messageQueue.length > 0 && this.isConnected()) {
      const message = this.messageQueue.shift()
      if (message) {
        this.send(message)
      }
    }
  }

  // 生成订阅键
  private generateSubscriptionKey(request: SubscriptionRequest): string {
    return `${request.symbols.join(',')}_${request.dataTypes.join(',')}_${request.interval || ''}`
  }

  // 生成消息ID
  private generateMessageId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  }

  // 销毁实例
  public destroy(): void {
    this.disconnect()
    this.clearSubscriptions()
    this.listeners.clear()
    this.messageQueue = []
  }
}

// 创建全局WebSocket管理器实例
let globalWebSocketManager: WebSocketManager | null = null

export function createWebSocketManager(config: WebSocketConfig): WebSocketManager {
  if (globalWebSocketManager) {
    globalWebSocketManager.destroy()
  }
  
  globalWebSocketManager = new WebSocketManager(config)
  return globalWebSocketManager
}

export function getWebSocketManager(): WebSocketManager | null {
  return globalWebSocketManager
}

// WebSocket工厂函数
export function createMarketWebSocket(): WebSocketManager {
  const wsUrl = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000/api/market/ws'
  
  return createWebSocketManager({
    url: wsUrl,
    heartbeatInterval: 30000,
    reconnectInterval: 5000,
    maxReconnectAttempts: 5,
    enableHeartbeat: true,
    enableReconnect: true
  })
}

export function createTradingWebSocket(): WebSocketManager {
  const wsUrl = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000/api/trading/ws'
  
  return createWebSocketManager({
    url: wsUrl,
    heartbeatInterval: 30000,
    reconnectInterval: 3000,
    maxReconnectAttempts: 10,
    enableHeartbeat: true,
    enableReconnect: true
  })
} 