/**
 * 数据流组合函数
 * 处理实时数据流订阅和管理
 */
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { getWebSocketService } from '@/services/websocket.service'
import type { Ref } from 'vue'
import { websocketService, MessageType, Channel } from '@/services/websocket.service'
import type { 
  TickData, 
  DepthData, 
  OrderData, 
  TradeData, 
  PositionData,
  StrategyData 
} from '@/types/api'

export interface DataStreamOptions {
  autoConnect?: boolean
  reconnectOnError?: boolean
  bufferSize?: number
  throttleMs?: number
}

export interface StreamData<T = any> {
  data: T
  timestamp: number
  sequence: number
}

export function useDataStream<T = any>(
  streamType: string,
  options: DataStreamOptions = {}
) {
  const {
    autoConnect = true,
    reconnectOnError = true,
    bufferSize = 1000,
    throttleMs = 0
  } = options

  // 状态
  const connected = ref(false)
  const loading = ref(false)
  const error = ref<Error | null>(null)
  const lastUpdate = ref<number>(0)
  
  // 数据
  const currentData = ref<T | null>(null)
  const dataBuffer = ref<StreamData<T>[]>([])
  const sequence = ref(0)

  // WebSocket 服务
  const wsService = getWebSocketService()
  
  // 节流控制
  let lastEmitTime = 0
  let throttleTimer: NodeJS.Timeout | null = null

  // 计算属性
  const isConnected = computed(() => connected.value && wsService.isConnected())
  const hasData = computed(() => currentData.value !== null)
  const bufferLength = computed(() => dataBuffer.value.length)

  /**
   * 连接数据流
   */
  const connect = async (): Promise<void> => {
    if (loading.value) return

    loading.value = true
    error.value = null

    try {
      if (!wsService.isConnected()) {
        await wsService.connect()
      }

      // 监听连接状态
      wsService.on('connect', handleConnect)
      wsService.on('disconnect', handleDisconnect)
      wsService.on('error', handleError)

      // 监听数据流
      wsService.on(streamType as any, handleDataReceived)

      // 订阅数据流
      wsService.emit('subscribe', { type: streamType })

      connected.value = true
    } catch (err) {
      error.value = err as Error
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 断开数据流
   */
  const disconnect = (): void => {
    if (!connected.value) return

    // 取消订阅
    wsService.emit('unsubscribe', { type: streamType })

    // 移除事件监听
    wsService.off('connect', handleConnect)
    wsService.off('disconnect', handleDisconnect)
    wsService.off('error', handleError)
    wsService.off(streamType as any, handleDataReceived)

    connected.value = false
    clearThrottleTimer()
  }

  /**
   * 发送消息到数据流
   */
  const send = (message: any): void => {
    if (!isConnected.value) {
      throw new Error('Data stream not connected')
    }

    wsService.emit(streamType, message)
  }

  /**
   * 清空数据缓冲区
   */
  const clearBuffer = (): void => {
    dataBuffer.value = []
  }

  /**
   * 获取历史数据
   */
  const getHistoryData = (count?: number): StreamData<T>[] => {
    if (count) {
      return dataBuffer.value.slice(-count)
    }
    return [...dataBuffer.value]
  }

  /**
   * 重置状态
   */
  const reset = (): void => {
    currentData.value = null
    dataBuffer.value = []
    sequence.value = 0
    lastUpdate.value = 0
    error.value = null
  }

  // 事件处理器

  const handleConnect = (): void => {
    connected.value = true
    error.value = null
  }

  const handleDisconnect = (): void => {
    connected.value = false
    if (reconnectOnError && !error.value) {
      // 自动重连
      setTimeout(() => {
        if (!connected.value) {
          connect().catch(console.error)
        }
      }, 3000)
    }
  }

  const handleError = (err: Error): void => {
    error.value = err
    if (reconnectOnError) {
      setTimeout(() => {
        connect().catch(console.error)
      }, 5000)
    }
  }

  const handleDataReceived = (data: T): void => {
    const now = Date.now()

    // 节流处理
    if (throttleMs > 0) {
      const timeSinceLastEmit = now - lastEmitTime
      if (timeSinceLastEmit < throttleMs) {
        // 设置延迟处理
        clearThrottleTimer()
        throttleTimer = setTimeout(() => {
          processData(data, now)
        }, throttleMs - timeSinceLastEmit)
        return
      }
    }

    processData(data, now)
  }

  const processData = (data: T, timestamp: number): void => {
    sequence.value++
    lastUpdate.value = timestamp
    lastEmitTime = timestamp

    // 更新当前数据
    currentData.value = data

    // 添加到缓冲区
    const streamData: StreamData<T> = {
      data,
      timestamp,
      sequence: sequence.value
    }

    dataBuffer.value.push(streamData)

    // 限制缓冲区大小
    if (dataBuffer.value.length > bufferSize) {
      dataBuffer.value.shift()
    }
  }

  const clearThrottleTimer = (): void => {
    if (throttleTimer) {
      clearTimeout(throttleTimer)
      throttleTimer = null
    }
  }

  // 生命周期
  onMounted(() => {
    if (autoConnect) {
      connect().catch(console.error)
    }
  })

  onUnmounted(() => {
    disconnect()
    clearThrottleTimer()
  })

  return {
    // 状态
    connected: isConnected,
    loading,
    error,
    lastUpdate,
    hasData,
    bufferLength,

    // 数据
    currentData: currentData as Ref<T | null>,
    dataBuffer: dataBuffer as Ref<StreamData<T>[]>,

    // 方法
    connect,
    disconnect,
    send,
    clearBuffer,
    getHistoryData,
    reset
  }
}

/**
 * 行情数据流
 */
export function useMarketDataStream() {
  const tickData = ref<Map<string, TickData>>(new Map())
  const depthData = ref<Map<string, DepthData>>(new Map())
  const klineData = ref<Map<string, any[]>>(new Map())
  const isConnected = ref(false)
  const subscribedSymbols = ref<Set<string>>(new Set())

  // 连接状态
  const connectionStatus = computed(() => ({
    connected: isConnected.value,
    subscribedCount: subscribedSymbols.value.size
  }))

  // 订阅实时行情
  const subscribeTick = (symbols: string[]) => {
    const unsubscribe = websocketService.subscribeMarketTick(symbols, (data: TickData) => {
      tickData.value.set(data.symbol, data)
    })

    symbols.forEach(symbol => subscribedSymbols.value.add(symbol))
    return unsubscribe
  }

  // 订阅深度数据
  const subscribeDepth = (symbol: string) => {
    const unsubscribe = websocketService.subscribeMarketDepth(symbol, (data: DepthData) => {
      depthData.value.set(symbol, data)
    })

    subscribedSymbols.value.add(symbol)
    return unsubscribe
  }

  // 订阅K线数据
  const subscribeKline = (symbol: string, interval: string) => {
    const unsubscribe = websocketService.subscribeMarketKline(symbol, interval, (data: any) => {
      const key = `${symbol}_${interval}`
      if (!klineData.value.has(key)) {
        klineData.value.set(key, [])
      }
      const klines = klineData.value.get(key)!
      klines.push(data)
      
      // 保持最新1000条K线
      if (klines.length > 1000) {
        klines.shift()
      }
    })

    subscribedSymbols.value.add(symbol)
    return unsubscribe
  }

  // 获取特定品种的实时行情
  const getTickBySymbol = (symbol: string) => {
    return computed(() => tickData.value.get(symbol))
  }

  // 获取特定品种的深度数据
  const getDepthBySymbol = (symbol: string) => {
    return computed(() => depthData.value.get(symbol))
  }

  // 获取特定品种的K线数据
  const getKlineBySymbol = (symbol: string, interval: string) => {
    return computed(() => klineData.value.get(`${symbol}_${interval}`) || [])
  }

  // 清除数据
  const clearData = () => {
    tickData.value.clear()
    depthData.value.clear()
    klineData.value.clear()
    subscribedSymbols.value.clear()
  }

  onMounted(() => {
    isConnected.value = websocketService.isConnectionActive()
    if (!isConnected.value) {
      websocketService.connect()
    }
  })

  return {
    // 数据
    tickData: computed(() => tickData.value),
    depthData: computed(() => depthData.value),
    klineData: computed(() => klineData.value),
    
    // 状态
    connectionStatus,
    
    // 方法
    subscribeTick,
    subscribeDepth,
    subscribeKline,
    getTickBySymbol,
    getDepthBySymbol,
    getKlineBySymbol,
    clearData
  }
}

/**
 * 交易数据流
 */
export function useTradingDataStream() {
  const orders = ref<OrderData[]>([])
  const trades = ref<TradeData[]>([])
  const positions = ref<PositionData[]>([])
  const account = ref<any>(null)
  const isConnected = ref(false)

  let unsubscribeOrders: (() => void) | null = null
  let unsubscribeTrades: (() => void) | null = null
  let unsubscribePositions: (() => void) | null = null
  let unsubscribeAccount: (() => void) | null = null

  // 订阅交易数据
  const subscribe = () => {
    // 订阅订单更新
    unsubscribeOrders = websocketService.subscribeTradingOrders((data: OrderData) => {
      const index = orders.value.findIndex(order => order.id === data.id)
      if (index >= 0) {
        orders.value[index] = data
      } else {
        orders.value.unshift(data)
      }
      
      // 保持最新100条订单
      if (orders.value.length > 100) {
        orders.value = orders.value.slice(0, 100)
      }
    })

    // 订阅成交更新
    unsubscribeTrades = websocketService.subscribeTradingTrades((data: TradeData) => {
      trades.value.unshift(data)
      
      // 保持最新100条成交
      if (trades.value.length > 100) {
        trades.value = trades.value.slice(0, 100)
      }
    })

    // 订阅持仓更新
    unsubscribePositions = websocketService.subscribeTradingPositions((data: PositionData) => {
      const index = positions.value.findIndex(pos => pos.symbol === data.symbol)
      if (index >= 0) {
        if (data.quantity === 0) {
          // 持仓为0，移除
          positions.value.splice(index, 1)
        } else {
          // 更新持仓
          positions.value[index] = data
        }
      } else if (data.quantity > 0) {
        // 新增持仓
        positions.value.push(data)
      }
    })

    // 订阅账户更新
    unsubscribeAccount = websocketService.subscribeTradingAccount((data: any) => {
      account.value = data
    })
  }

  // 取消订阅
  const unsubscribe = () => {
    unsubscribeOrders?.()
    unsubscribeTrades?.()
    unsubscribePositions?.()
    unsubscribeAccount?.()
  }

  // 清除数据
  const clearData = () => {
    orders.value = []
    trades.value = []
    positions.value = []
    account.value = null
  }

  // 获取特定订单
  const getOrderById = (orderId: string) => {
    return computed(() => orders.value.find(order => order.id === orderId))
  }

  // 获取特定品种的持仓
  const getPositionBySymbol = (symbol: string) => {
    return computed(() => positions.value.find(pos => pos.symbol === symbol))
  }

  // 获取账户统计
  const accountStats = computed(() => {
    if (!account.value) return null
    
    return {
      totalValue: account.value.totalValue || 0,
      availableCash: account.value.availableCash || 0,
      totalPnL: positions.value.reduce((sum, pos) => sum + (pos.unrealizedPnL || 0), 0),
      positionCount: positions.value.length,
      activeOrderCount: orders.value.filter(order => ['pending', 'partial'].includes(order.status)).length
    }
  })

  onMounted(() => {
    isConnected.value = websocketService.isConnectionActive()
    if (isConnected.value) {
      subscribe()
    }
  })

  onUnmounted(() => {
    unsubscribe()
  })

  return {
    // 数据
    orders: computed(() => orders.value),
    trades: computed(() => trades.value),
    positions: computed(() => positions.value),
    account: computed(() => account.value),
    accountStats,
    
    // 状态
    isConnected: computed(() => isConnected.value),
    
    // 方法
    subscribe,
    unsubscribe,
    clearData,
    getOrderById,
    getPositionBySymbol
  }
}

/**
 * 策略数据流
 */
export function useStrategyDataStream(strategyId?: string) {
  const strategyStatus = ref<StrategyData | null>(null)
  const strategyLogs = ref<any[]>([])
  const strategySignals = ref<any[]>([])
  const isConnected = ref(false)

  let unsubscribeStatus: (() => void) | null = null
  let unsubscribeLogs: (() => void) | null = null
  let unsubscribeSignals: (() => void) | null = null

  // 订阅策略数据
  const subscribe = (id: string) => {
    if (unsubscribeStatus) unsubscribeStatus()
    if (unsubscribeLogs) unsubscribeLogs()
    if (unsubscribeSignals) unsubscribeSignals()

    // 订阅策略状态
    unsubscribeStatus = websocketService.subscribeStrategyStatus(id, (data: StrategyData) => {
      strategyStatus.value = data
    })

    // 订阅策略日志
    unsubscribeLogs = websocketService.subscribeStrategyLogs(id, (data: any) => {
      strategyLogs.value.unshift(data)
      
      // 保持最新500条日志
      if (strategyLogs.value.length > 500) {
        strategyLogs.value = strategyLogs.value.slice(0, 500)
      }
    })

    // 订阅策略信号
    unsubscribeSignals = websocketService.subscribeStrategySignals(id, (data: any) => {
      strategySignals.value.unshift(data)
      
      // 保持最新100个信号
      if (strategySignals.value.length > 100) {
        strategySignals.value = strategySignals.value.slice(0, 100)
      }
    })
  }

  // 取消订阅
  const unsubscribe = () => {
    unsubscribeStatus?.()
    unsubscribeLogs?.()
    unsubscribeSignals?.()
  }

  // 清除数据
  const clearData = () => {
    strategyStatus.value = null
    strategyLogs.value = []
    strategySignals.value = []
  }

  // 过滤日志
  const getLogsByLevel = (level?: string) => {
    return computed(() => {
      if (!level) return strategyLogs.value
      return strategyLogs.value.filter(log => log.level === level)
    })
  }

  // 获取最新信号
  const getLatestSignals = (count: number = 10) => {
    return computed(() => strategySignals.value.slice(0, count))
  }

  onMounted(() => {
    isConnected.value = websocketService.isConnectionActive()
    if (isConnected.value && strategyId) {
      subscribe(strategyId)
    }
  })

  onUnmounted(() => {
    unsubscribe()
  })

  return {
    // 数据
    strategyStatus: computed(() => strategyStatus.value),
    strategyLogs: computed(() => strategyLogs.value),
    strategySignals: computed(() => strategySignals.value),
    
    // 状态
    isConnected: computed(() => isConnected.value),
    
    // 方法
    subscribe,
    unsubscribe,
    clearData,
    getLogsByLevel,
    getLatestSignals
  }
}

/**
 * 系统消息流
 */
export function useSystemMessageStream() {
  const notifications = ref<any[]>([])
  const alerts = ref<any[]>([])
  const isConnected = ref(false)

  let unsubscribeNotifications: (() => void) | null = null
  let unsubscribeAlerts: (() => void) | null = null

  // 订阅系统消息
  const subscribe = () => {
    // 订阅通知
    unsubscribeNotifications = websocketService.subscribeNotifications((data: any) => {
      notifications.value.unshift(data)
      
      // 保持最新50条通知
      if (notifications.value.length > 50) {
        notifications.value = notifications.value.slice(0, 50)
      }
    })

    // 订阅告警
    unsubscribeAlerts = websocketService.subscribeAlerts((data: any) => {
      alerts.value.unshift(data)
      
      // 保持最新20条告警
      if (alerts.value.length > 20) {
        alerts.value = alerts.value.slice(0, 20)
      }
    })
  }

  // 取消订阅
  const unsubscribe = () => {
    unsubscribeNotifications?.()
    unsubscribeAlerts?.()
  }

  // 清除数据
  const clearData = () => {
    notifications.value = []
    alerts.value = []
  }

  // 未读通知数量
  const unreadNotificationCount = computed(() => {
    return notifications.value.filter(n => !n.read).length
  })

  // 未读告警数量
  const unreadAlertCount = computed(() => {
    return alerts.value.filter(a => !a.read).length
  })

  onMounted(() => {
    isConnected.value = websocketService.isConnectionActive()
    if (isConnected.value) {
      subscribe()
    }
  })

  onUnmounted(() => {
    unsubscribe()
  })

  return {
    // 数据
    notifications: computed(() => notifications.value),
    alerts: computed(() => alerts.value),
    
    // 状态
    isConnected: computed(() => isConnected.value),
    unreadNotificationCount,
    unreadAlertCount,
    
    // 方法
    subscribe,
    unsubscribe,
    clearData
  }
}