/**
 * WebSocket 服务
 * 处理实时数据连接和消息管理
 * 使用原生 WebSocket API
 */
import { ElMessage } from 'element-plus'
import mitt from 'mitt'
import type { Emitter } from 'mitt'
import { useUserStore } from '@/stores/modules/user'
import { WebSocketManager } from '@/utils/websocket'
import type { 
  TickData,
  DepthData,
  OrderData,
  TradeData,
  PositionData,
  StrategyData
} from '@/types/api'

export interface WebSocketConfig {
  url: string
  protocols?: string[]
}

export interface WebSocketEvents {
  connect: void
  disconnect: void
  error: Event
  message: any
  reconnect: number
  'market-data': any
  'trading-update': any
  notification: any
  'system-message': any
}

// WebSocket服务专用消息接口
export interface WebSocketServiceMessage {
  type: string
  channel?: string
  data: any
  timestamp?: string
  id?: string
}

// WebSocket消息类型
export enum MessageType {
  // 行情数据
  TICK = 'tick',
  DEPTH = 'depth',
  KLINE = 'kline',
  
  // 交易数据
  ORDER = 'order',
  TRADE = 'trade',
  POSITION = 'position',
  ACCOUNT = 'account',
  
  // 策略数据
  STRATEGY_STATUS = 'strategy_status',
  STRATEGY_LOG = 'strategy_log',
  STRATEGY_SIGNAL = 'strategy_signal',
  
  // 系统消息
  NOTIFICATION = 'notification',
  ALERT = 'alert',
  HEARTBEAT = 'heartbeat'
}

// 订阅频道
export enum Channel {
  MARKET = 'market',
  TRADING = 'trading',
  STRATEGY = 'strategy',
  SYSTEM = 'system'
}

export class WebSocketService {
  private wsManager: WebSocketManager
  private subscriptions = new Map<string, Set<Function>>()
  private isConnected = false
  private eventEmitter: Emitter<WebSocketEvents>

  constructor() {
    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws'
    this.wsManager = new WebSocketManager({ url: wsUrl })
    this.eventEmitter = mitt<WebSocketEvents>()
    this.initialize()
  }

  private initialize() {
    // 连接状态监听
    this.wsManager.on('connected', () => {
      this.isConnected = true
      ElMessage.success('WebSocket连接成功')
      this.eventEmitter.emit('connect', undefined)
      this.resubscribeAll()
    })

    this.wsManager.on('disconnected', () => {
      this.isConnected = false
      ElMessage.warning('WebSocket连接断开')
      this.eventEmitter.emit('disconnect', undefined)
    })

    // 消息监听
    this.wsManager.on('message', (message: any) => {
      this.handleMessage(message)
      this.eventEmitter.emit('message', message)
    })

    // 错误处理
    this.wsManager.on('error', (error) => {
      console.error('WebSocket错误:', error)
      ElMessage.error('WebSocket连接错误')
      this.eventEmitter.emit('error', error)
    })
  }

  private handleMessage(message: WebSocketServiceMessage) {
    // 如果消息没有channel属性，尝试从type中解析
    let channel = message.channel
    let type = message.type
    
    if (!channel && message.type) {
      // 如果type是形如 "market.tick" 的格式，分割获取channel和type
      const parts = message.type.split('.')
      if (parts.length === 2) {
        channel = parts[0]
        type = parts[1]
      } else {
        // 默认根据消息类型推断channel
        if (['tick', 'depth', 'kline'].includes(type)) {
          channel = Channel.MARKET
        } else if (['order', 'trade', 'position', 'account'].includes(type)) {
          channel = Channel.TRADING
        } else if (['strategy_status', 'strategy_log', 'strategy_signal'].includes(type)) {
          channel = Channel.STRATEGY
        } else {
          channel = Channel.SYSTEM
        }
      }
    }
    
    if (channel && type) {
      const key = `${channel}:${type}`
      const callbacks = this.subscriptions.get(key)
      
      if (callbacks) {
        callbacks.forEach(callback => {
          try {
            callback(message.data)
          } catch (error) {
            console.error('WebSocket消息处理错误:', error)
          }
        })
      }
    }
  }

  private resubscribeAll() {
    // 重新订阅所有频道
    for (const key of this.subscriptions.keys()) {
      const [channel, type] = key.split(':')
      this.wsManager.send({
        action: 'subscribe',
        channel,
        type
      })
    }
  }

  // ============ 连接管理 ============

  connect() {
    return this.wsManager.connect()
  }

  disconnect() {
    this.wsManager.disconnect()
  }

  isConnectionActive() {
    return this.isConnected
  }

  // ============ 事件管理 ============

  on<K extends keyof WebSocketEvents>(event: K, handler: (data: WebSocketEvents[K]) => void) {
    this.eventEmitter.on(event, handler)
  }

  off<K extends keyof WebSocketEvents>(event: K, handler: (data: WebSocketEvents[K]) => void) {
    this.eventEmitter.off(event, handler)
  }

  // ============ 订阅管理 ============

  subscribe(channel: Channel, type: MessageType, callback: Function) {
    const key = `${channel}:${type}`
    
    if (!this.subscriptions.has(key)) {
      this.subscriptions.set(key, new Set())
      
      // 发送订阅请求
      if (this.isConnected) {
        this.wsManager.send({
          action: 'subscribe',
          channel,
          type
        })
      }
    }
    
    this.subscriptions.get(key)!.add(callback)
    
    // 返回取消订阅函数
    return () => {
      this.unsubscribe(channel, type, callback)
    }
  }

  unsubscribe(channel: Channel, type: MessageType, callback?: Function) {
    const key = `${channel}:${type}`
    const callbacks = this.subscriptions.get(key)
    
    if (callbacks) {
      if (callback) {
        callbacks.delete(callback)
        
        // 如果没有回调函数了，取消订阅
        if (callbacks.size === 0) {
          this.subscriptions.delete(key)
          
          if (this.isConnected) {
            this.wsManager.send({
              action: 'unsubscribe',
              channel,
              type
            })
          }
        }
      } else {
        // 取消所有回调
        this.subscriptions.delete(key)
        
        if (this.isConnected) {
          this.wsManager.send({
            action: 'unsubscribe',
            channel,
            type
          })
        }
      }
    }
  }

  // ============ 行情数据订阅 ============

  subscribeMarketTick(symbols: string[], callback: (data: TickData) => void) {
    const unsubscribe = this.subscribe(Channel.MARKET, MessageType.TICK, callback)
    
    // 订阅特定品种
    if (this.isConnected) {
      this.wsManager.send({
        action: 'subscribe',
        channel: Channel.MARKET,
        type: MessageType.TICK,
        symbols
      })
    }
    
    return unsubscribe
  }

  subscribeMarketDepth(symbol: string, callback: (data: DepthData) => void) {
    const unsubscribe = this.subscribe(Channel.MARKET, MessageType.DEPTH, callback)
    
    if (this.isConnected) {
      this.wsManager.send({
        action: 'subscribe',
        channel: Channel.MARKET,
        type: MessageType.DEPTH,
        symbol
      })
    }
    
    return unsubscribe
  }

  subscribeMarketKline(symbol: string, interval: string, callback: (data: any) => void) {
    const unsubscribe = this.subscribe(Channel.MARKET, MessageType.KLINE, callback)
    
    if (this.isConnected) {
      this.wsManager.send({
        action: 'subscribe',
        channel: Channel.MARKET,
        type: MessageType.KLINE,
        symbol,
        interval
      })
    }
    
    return unsubscribe
  }

  // ============ 交易数据订阅 ============

  subscribeTradingOrders(callback: (data: OrderData) => void) {
    return this.subscribe(Channel.TRADING, MessageType.ORDER, callback)
  }

  subscribeTradingTrades(callback: (data: TradeData) => void) {
    return this.subscribe(Channel.TRADING, MessageType.TRADE, callback)
  }

  subscribeTradingPositions(callback: (data: PositionData) => void) {
    return this.subscribe(Channel.TRADING, MessageType.POSITION, callback)
  }

  subscribeTradingAccount(callback: (data: any) => void) {
    return this.subscribe(Channel.TRADING, MessageType.ACCOUNT, callback)
  }

  // ============ 策略数据订阅 ============

  subscribeStrategyStatus(strategyId: string, callback: (data: StrategyData) => void) {
    const unsubscribe = this.subscribe(Channel.STRATEGY, MessageType.STRATEGY_STATUS, callback)
    
    if (this.isConnected) {
      this.wsManager.send({
        action: 'subscribe',
        channel: Channel.STRATEGY,
        type: MessageType.STRATEGY_STATUS,
        strategyId
      })
    }
    
    return unsubscribe
  }

  subscribeStrategyLogs(strategyId: string, callback: (data: any) => void) {
    const unsubscribe = this.subscribe(Channel.STRATEGY, MessageType.STRATEGY_LOG, callback)
    
    if (this.isConnected) {
      this.wsManager.send({
        action: 'subscribe',
        channel: Channel.STRATEGY,
        type: MessageType.STRATEGY_LOG,
        strategyId
      })
    }
    
    return unsubscribe
  }

  subscribeStrategySignals(strategyId: string, callback: (data: any) => void) {
    const unsubscribe = this.subscribe(Channel.STRATEGY, MessageType.STRATEGY_SIGNAL, callback)
    
    if (this.isConnected) {
      this.wsManager.send({
        action: 'subscribe',
        channel: Channel.STRATEGY,
        type: MessageType.STRATEGY_SIGNAL,
        strategyId
      })
    }
    
    return unsubscribe
  }

  // ============ 系统消息订阅 ============

  subscribeNotifications(callback: (data: any) => void) {
    return this.subscribe(Channel.SYSTEM, MessageType.NOTIFICATION, callback)
  }

  subscribeAlerts(callback: (data: any) => void) {
    return this.subscribe(Channel.SYSTEM, MessageType.ALERT, callback)
  }

  // ============ 发送消息 ============

  sendMessage(message: any) {
    this.wsManager.send(message)
  }

  // ============ 状态查询 ============

  getConnectionStats() {
    return {
      isConnected: this.isConnected,
      subscriptionCount: this.subscriptions.size,
      state: this.wsManager.getState()
    }
  }

  getSubscriptionCount() {
    return this.subscriptions.size
  }

  getActiveSubscriptions() {
    return Array.from(this.subscriptions.keys())
  }
}

// 创建单例实例
export const websocketService = new WebSocketService()

export default websocketService